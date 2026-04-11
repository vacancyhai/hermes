"""Unit tests for admission matching/recommendation engine."""

from datetime import date, datetime, timedelta, timezone

import pytest
from app.services.matching import (
    AGE_MATCH,
    CATEGORY_ELIGIBILITY_MATCH,
    EDUCATION_MATCH,
    RECENCY_BONUS,
    STATE_MATCH,
    _education_rank,
    _user_age,
    get_recommended_admissions,
)


def _make_exam(
    eligibility=None,
    exam_type="pg",
    stream="general",
    created_at=None,
    exam_date=None,
    status="active",
):
    """Helper to create mock Admission."""
    from unittest.mock import MagicMock

    exam = MagicMock()
    exam.eligibility = eligibility or {}
    exam.exam_type = exam_type
    exam.stream = stream
    exam.created_at = created_at or datetime(2024, 1, 1, tzinfo=timezone.utc)
    exam.exam_date = exam_date
    exam.status = status
    return exam


def _make_profile(
    preferred_states=None,
    preferred_categories=None,
    highest_qualification=None,
    category=None,
    date_of_birth=None,
):
    """Helper to create mock UserProfile."""
    from unittest.mock import MagicMock

    p = MagicMock()
    p.preferred_states = preferred_states or []
    p.preferred_categories = preferred_categories or []
    p.highest_qualification = highest_qualification
    p.category = category
    p.date_of_birth = date_of_birth
    return p


# --- get_recommended_admissions — no profile path ---


@pytest.mark.asyncio
async def test_get_recommended_admissions_no_profile():
    """When user has no profile, return newest exams sorted by created_at (DB-paginated)."""
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()

    today = date.today()
    exam1 = _make_exam(
        created_at=datetime(2024, 1, 10, tzinfo=timezone.utc),
        exam_date=today + timedelta(days=30),
    )
    exam2 = _make_exam(
        created_at=datetime(2024, 1, 20, tzinfo=timezone.utc),
        exam_date=today + timedelta(days=60),
    )

    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = None

    count_result = MagicMock()
    count_result.scalar.return_value = 2

    # DB returns newest first (ORDER BY created_at DESC at DB level)
    exams_result = MagicMock()
    exams_result.scalars.return_value.all.return_value = [exam2, exam1]

    db.execute = AsyncMock(side_effect=[profile_result, count_result, exams_result])

    exams, total = await get_recommended_admissions(
        user_id="some-uuid", db=db, limit=10, offset=0
    )
    assert total == 2
    assert exams[0] == exam2


@pytest.mark.asyncio
async def test_get_recommended_admissions_no_profile_pagination():
    """Offset/limit pagination works in the no-profile path (DB-level)."""
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()

    paged_exams = [MagicMock(), MagicMock()]

    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = None

    count_result = MagicMock()
    count_result.scalar.return_value = 5

    exams_result = MagicMock()
    exams_result.scalars.return_value.all.return_value = paged_exams

    db.execute = AsyncMock(side_effect=[profile_result, count_result, exams_result])

    exams, total = await get_recommended_admissions(
        user_id="uid", db=db, limit=2, offset=2
    )
    assert total == 5
    assert len(exams) == 2


# --- get_recommended_admissions — with profile / scoring ---


@pytest.mark.asyncio
async def test_get_recommended_admissions_state_match():
    """State match adds STATE_MATCH score."""
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()
    profile = _make_profile(preferred_states=["Maharashtra"])
    exam_match = _make_exam(eligibility={"states": ["Maharashtra", "Karnataka"]})
    exam_no_match = _make_exam(eligibility={"states": ["Delhi"]})

    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = profile
    exams_result = MagicMock()
    exams_result.scalars.return_value.all.return_value = [exam_no_match, exam_match]
    db.execute = AsyncMock(side_effect=[profile_result, exams_result])

    exams, total = await get_recommended_admissions(user_id="uid", db=db, limit=10)
    assert total == 2
    # exam_match should come first (higher score)
    assert exams[0] == exam_match


@pytest.mark.asyncio
async def test_get_recommended_admissions_category_match():
    """Category match adds CATEGORY_ELIGIBILITY_MATCH score."""
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()
    profile = _make_profile(category="OBC")
    exam_match = _make_exam(eligibility={"category": ["OBC", "General"]})
    exam_no_match = _make_exam(eligibility={"category": ["General"]})

    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = profile
    exams_result = MagicMock()
    exams_result.scalars.return_value.all.return_value = [exam_no_match, exam_match]
    db.execute = AsyncMock(side_effect=[profile_result, exams_result])

    exams, _ = await get_recommended_admissions(user_id="uid", db=db, limit=10)
    assert exams[0] == exam_match


@pytest.mark.asyncio
async def test_get_recommended_admissions_education_match():
    """Education match: user qualifies when user_edu_rank >= exam_edu_rank."""
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()
    profile = _make_profile(highest_qualification="graduate")
    exam_qualifies = _make_exam(eligibility={"qualification": "12th"})
    exam_overqualified = _make_exam(eligibility={"qualification": "phd"})

    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = profile
    exams_result = MagicMock()
    exams_result.scalars.return_value.all.return_value = [
        exam_overqualified,
        exam_qualifies,
    ]
    db.execute = AsyncMock(side_effect=[profile_result, exams_result])

    exams, _ = await get_recommended_admissions(user_id="uid", db=db, limit=10)
    # exam_qualifies gets education bonus, so it ranks first
    assert exams[0] == exam_qualifies


@pytest.mark.asyncio
async def test_get_recommended_admissions_age_match():
    """Age match: user within exam's eligibility range gets AGE_MATCH score."""
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()
    # User is 25 years old
    dob = date.today() - timedelta(days=25 * 365)
    profile = _make_profile(date_of_birth=dob)

    exam_match = _make_exam(eligibility={"age_min": 18, "age_max": 30})
    exam_no_match = _make_exam(eligibility={"age_min": 30, "age_max": 40})

    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = profile
    exams_result = MagicMock()
    exams_result.scalars.return_value.all.return_value = [exam_no_match, exam_match]
    db.execute = AsyncMock(side_effect=[profile_result, exams_result])

    exams, _ = await get_recommended_admissions(user_id="uid", db=db, limit=10)
    assert exams[0] == exam_match


@pytest.mark.asyncio
async def test_get_recommended_admissions_recency_bonus():
    """Recent exams (within 7 days) get RECENCY_BONUS score."""
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()
    profile = _make_profile(highest_qualification="graduate")

    old_exam = _make_exam(
        eligibility={"qualification": "graduate"},
        created_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    new_exam = _make_exam(
        eligibility={"qualification": "graduate"},
        created_at=datetime.now(timezone.utc),
    )

    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = profile
    exams_result = MagicMock()
    exams_result.scalars.return_value.all.return_value = [old_exam, new_exam]
    db.execute = AsyncMock(side_effect=[profile_result, exams_result])

    exams, _ = await get_recommended_admissions(user_id="uid", db=db, limit=10)
    # new_exam gets recency bonus (both get edu match, new_exam gets +1 recency)
    assert exams[0] == new_exam


@pytest.mark.asyncio
async def test_get_recommended_admissions_combined_scoring():
    """Multiple matching criteria combine scores correctly."""
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()
    dob = date.today() - timedelta(days=22 * 365)
    profile = _make_profile(
        preferred_states=["Delhi"],
        category="SC",
        highest_qualification="graduate",
        date_of_birth=dob,
    )

    # This exam matches all criteria
    exam_perfect = _make_exam(
        eligibility={
            "states": ["Delhi"],
            "category": ["SC", "ST", "General"],
            "qualification": "12th",
            "age_min": 18,
            "age_max": 30,
        },
        created_at=datetime.now(timezone.utc),
    )

    # This exam matches nothing
    exam_poor = _make_exam(
        eligibility={
            "states": ["Maharashtra"],
            "category": ["General"],
            "qualification": "phd",
            "age_min": 30,
            "age_max": 40,
        },
        created_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )

    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = profile
    exams_result = MagicMock()
    exams_result.scalars.return_value.all.return_value = [exam_poor, exam_perfect]
    db.execute = AsyncMock(side_effect=[profile_result, exams_result])

    exams, _ = await get_recommended_admissions(user_id="uid", db=db, limit=10)
    # exam_perfect should rank first with high combined score
    assert exams[0] == exam_perfect


@pytest.mark.asyncio
async def test_get_recommended_admissions_empty_profile_no_scoring():
    """Profile with all-empty prefs → falls back to newest-first (DB-paginated)."""
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()
    profile = _make_profile(
        preferred_states=[],
        preferred_categories=[],
        highest_qualification=None,
        category=None,
        date_of_birth=None,
    )

    exam = _make_exam()
    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = profile

    count_result = MagicMock()
    count_result.scalar.return_value = 1

    exams_result = MagicMock()
    exams_result.scalars.return_value.all.return_value = [exam]
    db.execute = AsyncMock(side_effect=[profile_result, count_result, exams_result])

    exams, total = await get_recommended_admissions(user_id="uid", db=db, limit=10)
    assert total == 1


@pytest.mark.asyncio
async def test_get_recommended_admissions_category_string():
    """Category as string (not list) in eligibility still matches."""
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()
    profile = _make_profile(category="OBC")
    exam = _make_exam(eligibility={"category": "OBC"})

    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = profile
    exams_result = MagicMock()
    exams_result.scalars.return_value.all.return_value = [exam]
    db.execute = AsyncMock(side_effect=[profile_result, exams_result])

    exams, total = await get_recommended_admissions(user_id="uid", db=db, limit=10)
    assert total == 1


@pytest.mark.asyncio
async def test_get_recommended_admissions_state_string():
    """State as string (not list) in eligibility still matches."""
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()
    profile = _make_profile(preferred_states=["Karnataka"])
    exam = _make_exam(eligibility={"location": "Karnataka"})

    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = profile
    exams_result = MagicMock()
    exams_result.scalars.return_value.all.return_value = [exam]
    db.execute = AsyncMock(side_effect=[profile_result, exams_result])

    exams, total = await get_recommended_admissions(user_id="uid", db=db, limit=10)
    assert total == 1


@pytest.mark.asyncio
async def test_get_recommended_admissions_min_qualification_key():
    """Education matching works with 'min_qualification' key."""
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()
    profile = _make_profile(highest_qualification="graduate")
    exam = _make_exam(eligibility={"min_qualification": "12th"})

    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = profile
    exams_result = MagicMock()
    exams_result.scalars.return_value.all.return_value = [exam]
    db.execute = AsyncMock(side_effect=[profile_result, exams_result])

    exams, _ = await get_recommended_admissions(user_id="uid", db=db, limit=10)
    assert len(exams) == 1


@pytest.mark.asyncio
async def test_get_recommended_admissions_age_flexible_keys():
    """Age matching works with 'min_age'/'max_age' keys."""
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()
    dob = date.today() - timedelta(days=20 * 365)
    profile = _make_profile(date_of_birth=dob)
    exam = _make_exam(eligibility={"min_age": 18, "max_age": 25})

    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = profile
    exams_result = MagicMock()
    exams_result.scalars.return_value.all.return_value = [exam]
    db.execute = AsyncMock(side_effect=[profile_result, exams_result])

    exams, _ = await get_recommended_admissions(user_id="uid", db=db, limit=10)
    assert len(exams) == 1


@pytest.mark.asyncio
async def test_get_recommended_admissions_pagination():
    """Pagination works correctly with scored results."""
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()
    profile = _make_profile(highest_qualification="graduate")

    exams = [_make_exam(eligibility={"qualification": "graduate"}) for _ in range(10)]

    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = profile
    exams_result = MagicMock()
    exams_result.scalars.return_value.all.return_value = exams
    db.execute = AsyncMock(side_effect=[profile_result, exams_result])

    page, total = await get_recommended_admissions(
        user_id="uid", db=db, limit=5, offset=0
    )
    assert total == 10
    assert len(page) == 5

    # Second page
    profile_result2 = MagicMock()
    profile_result2.scalar_one_or_none.return_value = profile
    exams_result2 = MagicMock()
    exams_result2.scalars.return_value.all.return_value = exams
    db.execute = AsyncMock(side_effect=[profile_result2, exams_result2])

    page2, total2 = await get_recommended_admissions(
        user_id="uid", db=db, limit=5, offset=5
    )
    assert total2 == 10
    assert len(page2) == 5
