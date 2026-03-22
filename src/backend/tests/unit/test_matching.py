"""Unit tests for the job matching / scoring engine."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.matching import (
    EDUCATION_LEVELS,
    _education_rank,
    get_recommended_jobs,
)


# --- _education_rank ---

def test_education_rank_known_levels():
    assert _education_rank("10th") == 0
    assert _education_rank("12th") == 1
    assert _education_rank("diploma") == 2
    assert _education_rank("graduate") == 3
    assert _education_rank("postgraduate") == 4
    assert _education_rank("phd") == 5


def test_education_rank_case_insensitive():
    assert _education_rank("Graduate") == _education_rank("graduate")
    assert _education_rank("PHD") == _education_rank("phd")


def test_education_rank_unknown():
    assert _education_rank("unknown-level") == -1


def test_education_rank_none():
    assert _education_rank(None) == -1


def test_education_rank_empty_string():
    assert _education_rank("") == -1


# --- get_recommended_jobs —— no profile path ---

@pytest.mark.asyncio
async def test_get_recommended_jobs_no_profile():
    """When user has no profile, return newest jobs sorted by created_at (DB-paginated)."""
    from unittest.mock import AsyncMock, MagicMock
    from datetime import datetime, timezone

    db = AsyncMock()

    # Execute calls: 1) profile → None, 2) count → 2, 3) paginated jobs
    today = date.today()
    job1 = MagicMock()
    job1.created_at = datetime(2024, 1, 10, tzinfo=timezone.utc)
    job1.application_end = today + timedelta(days=30)

    job2 = MagicMock()
    job2.created_at = datetime(2024, 1, 20, tzinfo=timezone.utc)
    job2.application_end = today + timedelta(days=60)

    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = None

    count_result = MagicMock()
    count_result.scalar.return_value = 2

    # DB returns newest first (ORDER BY created_at DESC at DB level)
    jobs_result = MagicMock()
    jobs_result.scalars.return_value.all.return_value = [job2, job1]

    db.execute = AsyncMock(side_effect=[profile_result, count_result, jobs_result])

    jobs, total = await get_recommended_jobs(user_id="some-uuid", db=db, limit=10, offset=0)
    assert total == 2
    assert jobs[0] == job2


@pytest.mark.asyncio
async def test_get_recommended_jobs_no_profile_pagination():
    """Offset/limit pagination works in the no-profile path (DB-level)."""
    from unittest.mock import AsyncMock, MagicMock
    from datetime import datetime, timezone

    db = AsyncMock()

    # DB returns the 2 jobs for offset=2, limit=2 (already paginated)
    paged_jobs = [MagicMock(), MagicMock()]

    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = None

    count_result = MagicMock()
    count_result.scalar.return_value = 5

    jobs_result = MagicMock()
    jobs_result.scalars.return_value.all.return_value = paged_jobs

    db.execute = AsyncMock(side_effect=[profile_result, count_result, jobs_result])

    jobs, total = await get_recommended_jobs(user_id="uid", db=db, limit=2, offset=2)
    assert total == 5
    assert len(jobs) == 2


# --- get_recommended_jobs — with profile / scoring ---

def _make_job(
    eligibility=None, vacancy_breakdown=None, qualification_level=None,
    created_at=None, application_end=None,
):
    from datetime import datetime, timezone
    j = MagicMock()
    j.eligibility = eligibility or {}
    j.vacancy_breakdown = vacancy_breakdown or {}
    j.qualification_level = qualification_level
    j.created_at = created_at or datetime(2024, 1, 1, tzinfo=timezone.utc)
    j.application_end = application_end
    return j


def _make_profile(
    preferred_states=None, preferred_categories=None, highest_qualification=None
):
    p = MagicMock()
    p.preferred_states = preferred_states or []
    p.preferred_categories = preferred_categories or []
    p.highest_qualification = highest_qualification
    return p


@pytest.mark.asyncio
async def test_get_recommended_jobs_state_match():
    """State match adds STATE_MATCH score."""
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()
    profile = _make_profile(preferred_states=["Maharashtra"])
    job_match = _make_job(eligibility={"states": ["Maharashtra", "Karnataka"]})
    job_no_match = _make_job(eligibility={"states": ["Delhi"]})

    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = profile
    jobs_result = MagicMock()
    jobs_result.scalars.return_value.all.return_value = [job_no_match, job_match]
    db.execute = AsyncMock(side_effect=[profile_result, jobs_result])

    jobs, total = await get_recommended_jobs(user_id="uid", db=db, limit=10)
    assert total == 2
    # job_match should come first (higher score)
    assert jobs[0] == job_match


@pytest.mark.asyncio
async def test_get_recommended_jobs_category_match():
    """Category match adds CATEGORY_MATCH score."""
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()
    profile = _make_profile(preferred_categories=["obc"])
    job_match = _make_job(vacancy_breakdown={"OBC": 50, "General": 100})
    job_no_match = _make_job(vacancy_breakdown={"General": 200})

    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = profile
    jobs_result = MagicMock()
    jobs_result.scalars.return_value.all.return_value = [job_no_match, job_match]
    db.execute = AsyncMock(side_effect=[profile_result, jobs_result])

    jobs, _ = await get_recommended_jobs(user_id="uid", db=db, limit=10)
    assert jobs[0] == job_match


@pytest.mark.asyncio
async def test_get_recommended_jobs_education_match():
    """Education match: user qualifies when user_edu_rank >= job_edu_rank."""
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()
    profile = _make_profile(highest_qualification="graduate")
    job_qualifies = _make_job(qualification_level="12th")
    job_overqualified = _make_job(qualification_level="phd")  # user doesn't qualify

    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = profile
    jobs_result = MagicMock()
    jobs_result.scalars.return_value.all.return_value = [job_overqualified, job_qualifies]
    db.execute = AsyncMock(side_effect=[profile_result, jobs_result])

    jobs, _ = await get_recommended_jobs(user_id="uid", db=db, limit=10)
    # job_qualifies gets education bonus, so it ranks first
    assert jobs[0] == job_qualifies


@pytest.mark.asyncio
async def test_get_recommended_jobs_recency_bonus():
    """Recent jobs (within 7 days) get RECENCY_BONUS score."""
    from datetime import datetime, timezone
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()
    profile = _make_profile()
    # Profile with no prefs - but has qualification set to trigger scoring path
    profile.highest_qualification = "graduate"

    old_job = _make_job(
        qualification_level="graduate",
        created_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    new_job = _make_job(
        qualification_level="graduate",
        created_at=datetime.now(timezone.utc),
    )

    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = profile
    jobs_result = MagicMock()
    jobs_result.scalars.return_value.all.return_value = [old_job, new_job]
    db.execute = AsyncMock(side_effect=[profile_result, jobs_result])

    jobs, _ = await get_recommended_jobs(user_id="uid", db=db, limit=10)
    # new_job gets recency bonus (both get edu match, new_job gets +1 recency)
    assert jobs[0] == new_job


@pytest.mark.asyncio
async def test_get_recommended_jobs_eligibility_string_state():
    """State as string (not list) in eligibility still matches."""
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()
    profile = _make_profile(preferred_states=["Delhi"])
    job = _make_job(eligibility={"location": "Delhi"})

    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = profile
    jobs_result = MagicMock()
    jobs_result.scalars.return_value.all.return_value = [job]
    db.execute = AsyncMock(side_effect=[profile_result, jobs_result])

    jobs, total = await get_recommended_jobs(user_id="uid", db=db, limit=10)
    assert total == 1


@pytest.mark.asyncio
async def test_get_recommended_jobs_empty_profile_no_scoring():
    """Profile with all-empty prefs → falls back to newest-first (DB-paginated)."""
    from datetime import datetime, timezone
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()
    profile = _make_profile(preferred_states=[], preferred_categories=[], highest_qualification=None)

    j = _make_job()
    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = profile

    count_result = MagicMock()
    count_result.scalar.return_value = 1

    jobs_result = MagicMock()
    jobs_result.scalars.return_value.all.return_value = [j]
    db.execute = AsyncMock(side_effect=[profile_result, count_result, jobs_result])

    jobs, total = await get_recommended_jobs(user_id="uid", db=db, limit=10)
    assert total == 1


@pytest.mark.asyncio
async def test_get_recommended_jobs_category_from_eligibility():
    """Category from eligibility dict (list form) is matched."""
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()
    profile = _make_profile(preferred_categories=["sc"])
    job = _make_job(eligibility={"category": ["SC", "ST"]})

    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = profile
    jobs_result = MagicMock()
    jobs_result.scalars.return_value.all.return_value = [job]
    db.execute = AsyncMock(side_effect=[profile_result, jobs_result])

    jobs, total = await get_recommended_jobs(user_id="uid", db=db, limit=10)
    assert total == 1
