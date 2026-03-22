"""Job matching engine — scores jobs against user profile preferences."""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_vacancy import JobVacancy
from app.models.user_profile import UserProfile

# Scoring weights
STATE_MATCH = 3
CATEGORY_MATCH = 3
EDUCATION_MATCH = 2
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


async def get_recommended_jobs(
    user_id,
    db: AsyncSession,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Return jobs ranked by profile match score.

    Returns (scored_jobs, total_count).
    """
    # Load profile
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()

    # Base query: active jobs with future (or null) deadlines
    today = date.today()
    base = select(JobVacancy).where(
        JobVacancy.status == "active",
        (JobVacancy.application_end >= today) | (JobVacancy.application_end.is_(None)),
    )

    result = await db.execute(base)
    jobs = result.scalars().all()

    if not profile or (
        not profile.preferred_states
        and not profile.preferred_categories
        and not profile.highest_qualification
    ):
        # No preferences — return newest active jobs
        jobs_sorted = sorted(jobs, key=lambda j: j.created_at, reverse=True)
        total = len(jobs_sorted)
        page = jobs_sorted[offset : offset + limit]
        return page, total

    # Score each job
    pref_states = {s.lower() for s in (profile.preferred_states or [])}
    pref_cats = {c.lower() for c in (profile.preferred_categories or [])}
    user_edu_rank = _education_rank(profile.highest_qualification)
    recency_cutoff = today - timedelta(days=RECENCY_DAYS)

    scored: list[tuple[int, date | None, JobVacancy]] = []
    for job in jobs:
        score = 0

        # State match via eligibility or vacancy_breakdown
        job_states = set()
        if job.eligibility and isinstance(job.eligibility, dict):
            for key in ("states", "state", "location"):
                val = job.eligibility.get(key)
                if isinstance(val, list):
                    job_states.update(s.lower() for s in val)
                elif isinstance(val, str):
                    job_states.add(val.lower())
        if pref_states & job_states:
            score += STATE_MATCH

        # Category match (general / obc / sc / st / ews)
        job_cats = set()
        if job.vacancy_breakdown and isinstance(job.vacancy_breakdown, dict):
            job_cats = {k.lower() for k in job.vacancy_breakdown}
        if job.eligibility and isinstance(job.eligibility, dict):
            cat_val = job.eligibility.get("category")
            if isinstance(cat_val, list):
                job_cats.update(c.lower() for c in cat_val)
            elif isinstance(cat_val, str):
                job_cats.add(cat_val.lower())
        if pref_cats & job_cats:
            score += CATEGORY_MATCH

        # Education match: user qualifies if their education rank >= job's requirement
        job_edu_rank = _education_rank(job.qualification_level)
        if user_edu_rank >= 0 and job_edu_rank >= 0 and user_edu_rank >= job_edu_rank:
            score += EDUCATION_MATCH

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
