"""Job matching engine — scores jobs against user profile preferences."""

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admit_card import AdmitCard
from app.models.answer_key import AnswerKey
from app.models.entrance_exam import EntranceExam
from app.models.job import Job
from app.models.result import Result
from app.models.user_profile import UserProfile

# Maximum candidates fetched from DB before in-memory scoring (avoids loading all jobs)
# NOTE: Users whose preferences best match jobs created beyond this window may not see
# those jobs in recommendations. This is a known trade-off to avoid loading all rows.
CANDIDATE_LIMIT = 500

# Scoring weights
STATE_MATCH = 3
CATEGORY_ELIGIBILITY_MATCH = 4  # user's actual reservation category is eligible
CATEGORY_PREF_MATCH = 2         # user's preferred categories include a job category
EDUCATION_MATCH = 2
AGE_MATCH = 2                   # user's age is within job's eligibility range
RECENCY_BONUS = 1
RECENCY_DAYS = 7

# Education level hierarchy (higher index = higher qualification)
EDUCATION_LEVELS = ["10th", "12th", "diploma", "graduate", "postgraduate", "phd"]


def _education_rank(level: str | None) -> int:
    if not level:
        return -1
    try:
        return EDUCATION_LEVELS.index(level.lower())
    except ValueError:
        return -1


def _user_age(date_of_birth: date | None) -> int | None:
    """Return user's age in years, or None if date_of_birth is unset."""
    if not date_of_birth:
        return None
    today = date.today()
    return today.year - date_of_birth.year - (
        (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
    )


async def get_recommended_jobs(
    user_id,
    db: AsyncSession,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Return jobs ranked by profile match score.

    Scoring criteria (descending priority):
      - User's reservation category (profile.category) is eligible: +4
      - State match:                                                   +3
      - User's preferred categories intersect job categories:          +2
      - Education level qualifies:                                     +2
      - Age within job's eligibility range:                            +2
      - Job posted within last 7 days:                                 +1

    Returns (scored_jobs, total_count).
    """
    # Load profile
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()

    # Base query: active jobs with future (or null) deadlines
    today = date.today()
    base_filter = (
        Job.status == "active",
        (Job.application_end >= today) | (Job.application_end.is_(None)),
    )

    has_prefs = profile and (
        profile.preferred_states
        or profile.preferred_categories
        or profile.highest_qualification
        or profile.category
        or profile.date_of_birth
    )

    if not has_prefs:
        # No preferences — return newest active jobs using DB-level pagination
        total = (await db.execute(
            select(func.count(Job.id)).where(*base_filter)
        )).scalar() or 0
        result = await db.execute(
            select(Job)
            .where(*base_filter)
            .order_by(Job.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    # True DB count with same base filter — run before candidate fetch so total
    # reflects all eligible jobs, not just the CANDIDATE_LIMIT scoring window.
    total = (await db.execute(
        select(func.count(Job.id)).where(*base_filter)
    )).scalar() or 0

    # Cap candidate pool at CANDIDATE_LIMIT to avoid loading all jobs into memory.
    # Jobs are pre-sorted by recency so the best candidates are always included.
    result = await db.execute(
        select(Job)
        .where(*base_filter)
        .order_by(Job.created_at.desc())
        .limit(CANDIDATE_LIMIT)
    )
    jobs = result.scalars().all()

    # Pre-compute user attributes for scoring
    pref_states = {s.lower() for s in (profile.preferred_states or [])}
    pref_cats = {c.lower() for c in (profile.preferred_categories or [])}
    user_category = profile.category.lower() if profile.category else None
    user_edu_rank = _education_rank(profile.highest_qualification)
    user_age = _user_age(profile.date_of_birth)
    recency_cutoff = today - timedelta(days=RECENCY_DAYS)

    scored: list[tuple[int, date | None, Job]] = []
    for job in jobs:
        score = 0

        # Build job's eligible category set from vacancy_breakdown keys + eligibility.category
        job_cats = set()
        if job.vacancy_breakdown and isinstance(job.vacancy_breakdown, dict):
            job_cats = {k.lower() for k in job.vacancy_breakdown}
        if job.eligibility and isinstance(job.eligibility, dict):
            cat_val = job.eligibility.get("category")
            if isinstance(cat_val, list):
                job_cats.update(c.lower() for c in cat_val)
            elif isinstance(cat_val, str):
                job_cats.add(cat_val.lower())

        # Category eligibility: user's actual reservation category is in the job's categories
        if user_category and (not job_cats or user_category in job_cats):
            score += CATEGORY_ELIGIBILITY_MATCH

        # State match via eligibility or vacancy_breakdown
        job_states = set()
        if job.eligibility and isinstance(job.eligibility, dict):
            for key in ("states", "state", "location"):
                val = job.eligibility.get(key)
                if isinstance(val, list):
                    job_states.update(s.lower() for s in val)
                elif isinstance(val, str):
                    job_states.add(val.lower())
        if pref_states and (not job_states or pref_states & job_states):
            score += STATE_MATCH

        # Preferred categories: user's opted-in categories intersect job categories
        if pref_cats & job_cats:
            score += CATEGORY_PREF_MATCH

        # Education match: user qualifies if their rank >= job's requirement
        job_edu_rank = _education_rank(job.qualification_level)
        if user_edu_rank >= 0 and job_edu_rank >= 0 and user_edu_rank >= job_edu_rank:
            score += EDUCATION_MATCH

        # Age match: user's age is within the job's eligibility range
        if user_age is not None and job.eligibility and isinstance(job.eligibility, dict):
            age_min = job.eligibility.get("age_min")
            age_max = job.eligibility.get("age_max")
            if age_min is not None or age_max is not None:
                age_ok = True
                if age_min is not None:
                    age_ok = age_ok and user_age >= int(age_min)
                if age_max is not None:
                    age_ok = age_ok and user_age <= int(age_max)
                if age_ok:
                    score += AGE_MATCH

        # Recency bonus
        if job.created_at and job.created_at.date() >= recency_cutoff:
            score += RECENCY_BONUS

        scored.append((score, job.application_end, job))

    # Sort: score DESC, then deadline ASC (None deadlines last)
    far_future = date(9999, 12, 31)
    scored.sort(key=lambda t: (-t[0], t[1] or far_future))

    page = scored[offset : offset + limit]
    return [t[2] for t in page], total


async def _get_watched_ids(user_id, db: AsyncSession) -> tuple[list, list]:
    """Return (watched_job_ids, watched_exam_ids) for a user."""
    from app.models.user_watch import UserWatch
    result = await db.execute(
        select(UserWatch.entity_type, UserWatch.entity_id)
        .where(UserWatch.user_id == user_id)
    )
    rows = result.all()
    job_ids = [r.entity_id for r in rows if r.entity_type == "job"]
    exam_ids = [r.entity_id for r in rows if r.entity_type == "exam"]
    return job_ids, exam_ids


async def get_recommended_admit_cards(
    user_id,
    db: AsyncSession,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list, int]:
    """Return admit cards for jobs/exams the user is watching."""
    job_ids, exam_ids = await _get_watched_ids(user_id, db)
    if not job_ids and not exam_ids:
        return [], 0
    from sqlalchemy import or_
    result = await db.execute(
        select(AdmitCard)
        .where(
            or_(
                AdmitCard.job_id.in_(job_ids) if job_ids else False,
                AdmitCard.exam_id.in_(exam_ids) if exam_ids else False,
            )
        )
        .order_by(AdmitCard.published_at.desc())
    )
    cards = list(result.scalars().all())
    total = len(cards)
    return cards[offset : offset + limit], total


async def get_recommended_answer_keys(
    user_id,
    db: AsyncSession,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list, int]:
    """Return answer keys for jobs/exams the user is watching."""
    job_ids, exam_ids = await _get_watched_ids(user_id, db)
    if not job_ids and not exam_ids:
        return [], 0
    from sqlalchemy import or_
    result = await db.execute(
        select(AnswerKey)
        .where(
            or_(
                AnswerKey.job_id.in_(job_ids) if job_ids else False,
                AnswerKey.exam_id.in_(exam_ids) if exam_ids else False,
            )
        )
        .order_by(AnswerKey.published_at.desc())
    )
    keys = list(result.scalars().all())
    total = len(keys)
    return keys[offset : offset + limit], total


async def get_recommended_results(
    user_id,
    db: AsyncSession,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list, int]:
    """Return results for jobs/exams the user is watching."""
    job_ids, exam_ids = await _get_watched_ids(user_id, db)
    if not job_ids and not exam_ids:
        return [], 0
    from sqlalchemy import or_
    result = await db.execute(
        select(Result)
        .where(
            or_(
                Result.job_id.in_(job_ids) if job_ids else False,
                Result.exam_id.in_(exam_ids) if exam_ids else False,
            )
        )
        .order_by(Result.published_at.desc())
    )
    results_list = list(result.scalars().all())
    total = len(results_list)
    return results_list[offset : offset + limit], total


async def get_recommended_entrance_exams(
    user_id,
    db: AsyncSession,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Return entrance exams ranked by profile match score.

    Scoring criteria (descending priority):
      - User's reservation category is eligible:                +4
      - State match:                                             +3
      - Education level qualifies:                               +2
      - Age within exam's eligibility range:                     +2
      - Exam posted within last 7 days:                          +1

    Returns (scored_exams, total_count).
    """
    # Load profile
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    # Base query: active exams with future (or null) exam dates
    today = date.today()
    base_filter = (
        EntranceExam.status == "active",
        (EntranceExam.exam_date >= today) | (EntranceExam.exam_date.is_(None)),
    )
    
    has_prefs = profile and (
        profile.preferred_states
        or profile.highest_qualification
        or profile.category
        or profile.date_of_birth
    )
    
    if not has_prefs:
        # No preferences — return newest active exams using DB-level pagination
        total = (await db.execute(
            select(func.count(EntranceExam.id)).where(*base_filter)
        )).scalar() or 0
        result = await db.execute(
            select(EntranceExam)
            .where(*base_filter)
            .order_by(EntranceExam.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total
    
    # True DB count with same base filter — run before candidate fetch.
    total = (await db.execute(
        select(func.count(EntranceExam.id)).where(*base_filter)
    )).scalar() or 0

    # Cap candidate pool at CANDIDATE_LIMIT to avoid loading all exams into memory.
    # Exams are pre-sorted by recency so the best candidates are always included.
    result = await db.execute(
        select(EntranceExam)
        .where(*base_filter)
        .order_by(EntranceExam.created_at.desc())
        .limit(CANDIDATE_LIMIT)
    )
    exams = result.scalars().all()
    
    # Pre-compute user attributes for scoring
    pref_states = {s.lower() for s in (profile.preferred_states or [])}
    user_category = profile.category.lower() if profile.category else None
    user_edu_rank = _education_rank(profile.highest_qualification)
    user_age = _user_age(profile.date_of_birth)
    recency_cutoff = today - timedelta(days=RECENCY_DAYS)
    
    scored: list[tuple[int, date | None, EntranceExam]] = []
    for exam in exams:
        score = 0
        
        # Build exam's eligible category set from eligibility dict
        exam_cats = set()
        if exam.eligibility and isinstance(exam.eligibility, dict):
            cat_val = exam.eligibility.get("category")
            if isinstance(cat_val, list):
                exam_cats = {c.lower() for c in cat_val}
            elif isinstance(cat_val, str):
                exam_cats.add(cat_val.lower())
        
        # Category eligibility: user's actual reservation category is in the exam's categories
        if user_category and (not exam_cats or user_category in exam_cats):
            score += CATEGORY_ELIGIBILITY_MATCH
        
        # State match via eligibility dict
        exam_states = set()
        if exam.eligibility and isinstance(exam.eligibility, dict):
            for key in ("states", "state", "location", "conducting_states"):
                val = exam.eligibility.get(key)
                if isinstance(val, list):
                    exam_states.update(s.lower() for s in val)
                elif isinstance(val, str):
                    exam_states.add(val.lower())
        if pref_states and (not exam_states or pref_states & exam_states):
            score += STATE_MATCH
        
        # Education match: extract qualification from eligibility dict
        exam_edu_rank = -1
        if exam.eligibility and isinstance(exam.eligibility, dict):
            qual = exam.eligibility.get("qualification") or exam.eligibility.get("min_qualification")
            if qual:
                exam_edu_rank = _education_rank(qual)
        if user_edu_rank >= 0 and exam_edu_rank >= 0 and user_edu_rank >= exam_edu_rank:
            score += EDUCATION_MATCH
        
        # Age match: user's age is within the exam's eligibility range
        if user_age is not None and exam.eligibility and isinstance(exam.eligibility, dict):
            age_min = exam.eligibility.get("age_min") or exam.eligibility.get("min_age")
            age_max = exam.eligibility.get("age_max") or exam.eligibility.get("max_age")
            if age_min is not None or age_max is not None:
                age_ok = True
                if age_min is not None:
                    age_ok = age_ok and user_age >= int(age_min)
                if age_max is not None:
                    age_ok = age_ok and user_age <= int(age_max)
                if age_ok:
                    score += AGE_MATCH
        
        # Recency bonus
        if exam.created_at and exam.created_at.date() >= recency_cutoff:
            score += RECENCY_BONUS
        
        scored.append((score, exam.exam_date, exam))
    
    # Sort: score DESC, then exam_date ASC (None exam_dates last)
    far_future = date(9999, 12, 31)
    scored.sort(key=lambda t: (-t[0], t[1] or far_future))
    
    page = scored[offset : offset + limit]
    return [t[2] for t in page], total
