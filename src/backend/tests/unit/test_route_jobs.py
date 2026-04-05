"""Direct unit tests for jobs route handlers."""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_job(**kwargs):
    j = MagicMock()
    j.id = uuid.uuid4()
    j.job_title = kwargs.get("job_title", "Test Job")
    j.slug = kwargs.get("slug", "test-job")
    j.organization = kwargs.get("organization", "Test Org")
    j.status = kwargs.get("status", "active")
    j.qualification_level = kwargs.get("qualification_level", None)
    j.department = kwargs.get("department", None)
    j.is_featured = kwargs.get("is_featured", False)
    j.is_urgent = kwargs.get("is_urgent", False)
    j.created_at = datetime.now(timezone.utc)
    j.views = 0
    # Additional fields for JobListItem
    j.total_vacancies = None
    j.application_end = None
    j.short_description = None
    j.fee_general = None
    j.published_at = None
    return j


# ─── list_jobs ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_jobs_with_qualification_filter():
    from app.routers.jobs import list_jobs
    db = AsyncMock()
    count_result = MagicMock()
    count_result.scalar.return_value = 0
    data_result = MagicMock()
    data_result.scalars.return_value.all.return_value = []
    db.execute.side_effect = [count_result, data_result]

    output = await list_jobs(
        q=None, qualification_level="graduate",
        organization=None, department=None,
        is_featured=None, is_urgent=None,
        limit=20, offset=0, db=db,
    )
    assert output["data"] == []


@pytest.mark.asyncio
async def test_list_jobs_with_department_filter():
    from app.routers.jobs import list_jobs
    db = AsyncMock()
    count_result = MagicMock()
    count_result.scalar.return_value = 0
    data_result = MagicMock()
    data_result.scalars.return_value.all.return_value = []
    db.execute.side_effect = [count_result, data_result]

    output = await list_jobs(
        q=None, qualification_level=None,
        organization=None, department="Engineering",
        is_featured=None, is_urgent=None,
        limit=20, offset=0, db=db,
    )
    assert output["data"] == []


@pytest.mark.asyncio
async def test_list_jobs_with_featured_filter():
    from app.routers.jobs import list_jobs
    db = AsyncMock()
    count_result = MagicMock()
    count_result.scalar.return_value = 0
    data_result = MagicMock()
    data_result.scalars.return_value.all.return_value = []
    db.execute.side_effect = [count_result, data_result]

    output = await list_jobs(
        q=None, qualification_level=None,
        organization=None, department=None,
        is_featured=True, is_urgent=None,
        limit=20, offset=0, db=db,
    )
    assert output["pagination"]["total"] == 0


@pytest.mark.asyncio
async def test_list_jobs_with_urgent_filter():
    from app.routers.jobs import list_jobs
    db = AsyncMock()
    count_result = MagicMock()
    count_result.scalar.return_value = 0
    data_result = MagicMock()
    data_result.scalars.return_value.all.return_value = []
    db.execute.side_effect = [count_result, data_result]

    output = await list_jobs(
        q=None, qualification_level=None,
        organization=None, department=None,
        is_featured=None, is_urgent=True,
        limit=20, offset=0, db=db,
    )
    assert output["data"] == []


# ─── recommended_jobs ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_recommended_jobs():
    from app.routers.jobs import recommended_jobs
    from unittest.mock import patch

    user = MagicMock()
    user.id = uuid.uuid4()

    with patch("app.routers.jobs.get_recommended_jobs") as mock_get:
        mock_get.return_value = ([], 0)
        db = AsyncMock()
        output = await recommended_jobs(
            limit=20, offset=0,
            current_user=(user, {}), db=db,
        )

    assert output["data"] == []
    assert output["pagination"]["total"] == 0


# ─── get_job ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_job_found():
    from unittest.mock import patch
    from app.routers.jobs import get_job
    from app.schemas.jobs import JobResponse
    job = _make_job()

    select_result = MagicMock()
    select_result.scalar_one_or_none.return_value = job
    empty_result = MagicMock()
    empty_result.scalars.return_value.all.return_value = []
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[select_result, empty_result, empty_result, empty_result, empty_result])

    mock_response = MagicMock()
    mock_response.model_dump.return_value = {"id": str(job.id), "slug": "test-job"}
    with patch.object(JobResponse, "model_validate", return_value=mock_response):
        await get_job(job_id=job.id, db=db)


@pytest.mark.asyncio
async def test_get_job_not_found():
    from fastapi import HTTPException
    from app.routers.jobs import get_job
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc_info:
        await get_job(job_id=uuid.uuid4(), db=db)
    assert exc_info.value.status_code == 404
