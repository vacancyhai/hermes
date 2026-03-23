"""Direct unit tests for application route handlers with mocked dependencies.

Calls route functions directly (bypassing HTTP/ASGI) to avoid SQLAlchemy
greenlet coverage gaps. Provides full line coverage of the function bodies.
"""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_current_user(user_id=None):
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    return user, {"user_type": "user"}


def _make_app(user_id=None, status="applied"):
    """Create a mock UserJobApplication with all required fields for Pydantic validation."""
    app = MagicMock()
    app.id = uuid.uuid4()
    app.user_id = user_id or uuid.uuid4()
    app.job_id = uuid.uuid4()
    app.status = status
    app.notes = None
    app.application_number = None
    app.is_priority = False
    app.applied_on = datetime.now(timezone.utc)
    app.updated_at = datetime.now(timezone.utc)
    app.reminders = []
    app.result_info = {}
    return app


# ─── application_stats ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_application_stats_with_data():
    from app.routers.applications import application_stats
    db = AsyncMock()
    result = MagicMock()
    result.all.return_value = [("applied", 5), ("selected", 2)]
    db.execute.return_value = result

    output = await application_stats(current_user=_make_current_user(), db=db)
    assert output["total"] == 7
    assert output["applied"] == 5
    assert output["selected"] == 2


@pytest.mark.asyncio
async def test_application_stats_empty():
    from app.routers.applications import application_stats
    db = AsyncMock()
    result = MagicMock()
    result.all.return_value = []
    db.execute.return_value = result

    output = await application_stats(current_user=_make_current_user(), db=db)
    assert output["total"] == 0


# ─── list_applications ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_applications_no_filters():
    from app.routers.applications import list_applications
    db = AsyncMock()
    count_result = MagicMock()
    count_result.scalar.return_value = 0
    data_result = MagicMock()
    data_result.scalars.return_value.all.return_value = []
    db.execute.side_effect = [count_result, data_result]

    output = await list_applications(
        status_filter=None, is_priority=None, limit=20, offset=0,
        current_user=_make_current_user(), db=db,
    )
    assert output["pagination"]["total"] == 0
    assert output["data"] == []


@pytest.mark.asyncio
async def test_list_applications_with_status_filter():
    from app.routers.applications import list_applications
    db = AsyncMock()
    count_result = MagicMock()
    count_result.scalar.return_value = 1
    data_result = MagicMock()
    data_result.scalars.return_value.all.return_value = [_make_app()]
    job_result = MagicMock()
    job_result.scalar_one_or_none.return_value = None
    db.execute.side_effect = [count_result, data_result, job_result]

    output = await list_applications(
        status_filter="applied", is_priority=None, limit=20, offset=0,
        current_user=_make_current_user(), db=db,
    )
    assert output["pagination"]["total"] == 1


@pytest.mark.asyncio
async def test_list_applications_with_priority_filter():
    from app.routers.applications import list_applications
    db = AsyncMock()
    count_result = MagicMock()
    count_result.scalar.return_value = 0
    data_result = MagicMock()
    data_result.scalars.return_value.all.return_value = []
    db.execute.side_effect = [count_result, data_result]

    output = await list_applications(
        status_filter=None, is_priority=True, limit=20, offset=0,
        current_user=_make_current_user(), db=db,
    )
    assert output["data"] == []


@pytest.mark.asyncio
async def test_list_applications_with_job_enrichment():
    from app.routers.applications import list_applications
    db = AsyncMock()
    count_result = MagicMock()
    count_result.scalar.return_value = 1

    app_obj = _make_app()
    data_result = MagicMock()
    data_result.scalars.return_value.all.return_value = [app_obj]

    job = MagicMock()
    job.job_title = "SSC CGL 2024"
    job.slug = "ssc-cgl-2024"
    job.organization = "SSC"
    job.application_end = date(2025, 6, 30)

    jobs_result = MagicMock()
    jobs_result.scalars.return_value.all.return_value = [job]

    db.execute.side_effect = [count_result, data_result, jobs_result]

    output = await list_applications(
        status_filter=None, is_priority=None, limit=20, offset=0,
        current_user=_make_current_user(), db=db,
    )
    assert output["data"][0]["job"]["job_title"] == "SSC CGL 2024"


# ─── track_job ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_track_job_success():
    from unittest.mock import patch
    from app.routers.applications import track_job
    from app.schemas.applications import ApplicationCreateRequest, ApplicationResponse
    db = AsyncMock()

    job = MagicMock()
    job.id = uuid.uuid4()
    job.job_title = "UPSC IAS"
    job.slug = "upsc-ias"
    job.organization = "UPSC"
    job.application_end = None
    job.applications_count = 5

    job_result = MagicMock()
    job_result.scalar_one_or_none.return_value = job
    no_existing = MagicMock()
    no_existing.scalar_one_or_none.return_value = None

    db.execute.side_effect = [job_result, no_existing]
    db.flush = AsyncMock()

    mock_app_response = MagicMock()
    mock_app_response.model_dump.return_value = {"id": str(uuid.uuid4()), "status": "applied"}

    with patch.object(ApplicationResponse, "model_validate", return_value=mock_app_response):
        body = ApplicationCreateRequest(job_id=str(job.id))
        output = await track_job(body=body, current_user=_make_current_user(), db=db)

    assert output["job"]["job_title"] == "UPSC IAS"
    assert job.applications_count == 6


@pytest.mark.asyncio
async def test_track_job_not_found():
    from fastapi import HTTPException
    from app.routers.applications import track_job
    from app.schemas.applications import ApplicationCreateRequest
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    body = ApplicationCreateRequest(job_id=str(uuid.uuid4()))
    with pytest.raises(HTTPException) as exc_info:
        await track_job(body=body, current_user=_make_current_user(), db=db)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_track_job_duplicate():
    from fastapi import HTTPException
    from app.routers.applications import track_job
    from app.schemas.applications import ApplicationCreateRequest
    db = AsyncMock()
    job_result = MagicMock()
    job_result.scalar_one_or_none.return_value = MagicMock()
    existing_result = MagicMock()
    existing_result.scalar_one_or_none.return_value = MagicMock()
    db.execute.side_effect = [job_result, existing_result]

    body = ApplicationCreateRequest(job_id=str(uuid.uuid4()))
    with pytest.raises(HTTPException) as exc_info:
        await track_job(body=body, current_user=_make_current_user(), db=db)
    assert exc_info.value.status_code == 409


# ─── get_application ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_application_found():
    from app.routers.applications import get_application
    user_id = uuid.uuid4()
    app_obj = _make_app(user_id=user_id)
    app_obj.notes = "My notes"

    db = AsyncMock()
    app_result = MagicMock()
    app_result.scalar_one_or_none.return_value = app_obj

    job = MagicMock()
    job.job_title = "RRB NTPC"
    job.slug = "rrb-ntpc"
    job.organization = "RRB"
    job.application_end = None
    job_result = MagicMock()
    job_result.scalar_one_or_none.return_value = job

    db.execute.side_effect = [app_result, job_result]

    output = await get_application(
        application_id=app_obj.id,
        current_user=(MagicMock(id=user_id), {}),
        db=db,
    )
    assert output["notes"] == "My notes"
    assert output["job"]["job_title"] == "RRB NTPC"


@pytest.mark.asyncio
async def test_get_application_not_found():
    from fastapi import HTTPException
    from app.routers.applications import get_application
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    with pytest.raises(HTTPException) as exc_info:
        await get_application(
            application_id=uuid.uuid4(),
            current_user=_make_current_user(),
            db=db,
        )
    assert exc_info.value.status_code == 404


# ─── update_application ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_application_success():
    from app.routers.applications import update_application
    from app.schemas.applications import ApplicationUpdateRequest
    app_obj = _make_app()

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = app_obj
    db.execute.return_value = result

    body = ApplicationUpdateRequest(status="selected", is_priority=True)
    output = await update_application(
        application_id=app_obj.id, body=body,
        current_user=_make_current_user(), db=db,
    )
    assert app_obj.status == "selected"
    assert app_obj.is_priority is True


@pytest.mark.asyncio
async def test_update_application_invalid_status():
    from fastapi import HTTPException
    from app.routers.applications import update_application
    from app.schemas.applications import ApplicationUpdateRequest
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = _make_app()
    db.execute.return_value = result

    body = ApplicationUpdateRequest(status="invalid_status")
    with pytest.raises(HTTPException) as exc_info:
        await update_application(
            application_id=uuid.uuid4(), body=body,
            current_user=_make_current_user(), db=db,
        )
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_update_application_not_found():
    from fastapi import HTTPException
    from app.routers.applications import update_application
    from app.schemas.applications import ApplicationUpdateRequest
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    body = ApplicationUpdateRequest(notes="test")
    with pytest.raises(HTTPException) as exc_info:
        await update_application(
            application_id=uuid.uuid4(), body=body,
            current_user=_make_current_user(), db=db,
        )
    assert exc_info.value.status_code == 404


# ─── remove_application ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_remove_application_success():
    from app.routers.applications import remove_application
    app_obj = _make_app()

    job = MagicMock()
    job.applications_count = 3

    db = AsyncMock()
    app_result = MagicMock()
    app_result.scalar_one_or_none.return_value = app_obj
    job_result = MagicMock()
    job_result.scalar_one_or_none.return_value = job
    db.execute.side_effect = [app_result, job_result]
    db.delete = AsyncMock()

    await remove_application(
        application_id=app_obj.id,
        current_user=_make_current_user(), db=db,
    )
    assert job.applications_count == 2
    db.delete.assert_called_once_with(app_obj)


@pytest.mark.asyncio
async def test_remove_application_not_found():
    from fastapi import HTTPException
    from app.routers.applications import remove_application
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    with pytest.raises(HTTPException) as exc_info:
        await remove_application(
            application_id=uuid.uuid4(),
            current_user=_make_current_user(), db=db,
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_remove_application_job_count_zero():
    from app.routers.applications import remove_application
    app_obj = _make_app()
    job = MagicMock()
    job.applications_count = 0

    db = AsyncMock()
    app_result = MagicMock()
    app_result.scalar_one_or_none.return_value = app_obj
    job_result = MagicMock()
    job_result.scalar_one_or_none.return_value = job
    db.execute.side_effect = [app_result, job_result]
    db.delete = AsyncMock()

    await remove_application(
        application_id=app_obj.id,
        current_user=_make_current_user(), db=db,
    )
    assert job.applications_count == 0  # not decremented below 0
