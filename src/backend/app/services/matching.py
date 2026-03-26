"""Job matching engine — scores jobs against user profile preferences."""

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
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

    total = len(scored)
    page = scored[offset : offset + limit]
    return [t[2] for t in page], total
