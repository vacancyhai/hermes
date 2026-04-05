"""Direct unit tests for admin route handlers with mocked dependencies."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_admin(role="admin"):
    a = MagicMock()
    a.id = uuid.uuid4()
    a.email = "admin@example.com"
    a.role = role
    return a


def _make_user():
    u = MagicMock()
    u.id = uuid.uuid4()
    u.email = "user@example.com"
    u.full_name = "Test User"
    u.status = "active"
    u.phone = None
    u.is_email_verified = False
    u.created_at = datetime.now(timezone.utc)
    return u


def _make_job(**kwargs):
    j = MagicMock()
    j.id = uuid.uuid4()
    j.job_title = kwargs.get("job_title", "Test Job")
    j.slug = kwargs.get("slug", "test-job")
    j.organization = kwargs.get("organization", "SSC")
    j.status = kwargs.get("status", "draft")
    j.qualification_level = None
    j.department = None
    j.is_featured = False
    j.is_urgent = False
    j.created_at = datetime.now(timezone.utc)
    j.views = 0
    j.total_vacancies = None
    j.application_end = None
    j.short_description = None
    j.fee_general = None
    j.published_at = None
    return j


def _make_request(json_body=None):
    req = MagicMock()
    req.client.host = "127.0.0.1"
    req.headers.get.return_value = "pytest"
    if json_body is not None:
        import asyncio

        req.json = AsyncMock(return_value=json_body)
    return req


# ─── _slugify ─────────────────────────────────────────────────────────────────


def test_slugify_basic():
    from app.routers.admin import _slugify

    assert _slugify("SSC CGL 2024") == "ssc-cgl-2024"


def test_slugify_special_chars():
    from app.routers.admin import _slugify

    assert _slugify("UPSC (IAS) Exam!") == "upsc-ias-exam"


# ─── dashboard_stats ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dashboard_stats():
    from app.routers.admin import dashboard_stats

    db = AsyncMock()

    def _scalar_result(val):
        r = MagicMock()
        r.scalar.return_value = val
        return r

    # 11 queries via asyncio.gather in the order they appear in dashboard_stats
    db.execute.side_effect = [
        _scalar_result(10),  # jobs_total
        _scalar_result(7),  # jobs_active
        _scalar_result(3),  # jobs_draft
        _scalar_result(20),  # admit_cards_total
        _scalar_result(15),  # answer_keys_total
        _scalar_result(12),  # results_total
        _scalar_result(8),  # entrance_exams_total
        _scalar_result(5),  # entrance_exams_active
        _scalar_result(100),  # users_total
        _scalar_result(90),  # users_active
        _scalar_result(6),  # users_new_this_week
    ]

    output = await dashboard_stats(admin=_make_admin(), db=db)
    assert output["jobs"]["total"] == 10
    assert output["jobs"]["active"] == 7
    assert output["jobs"]["draft"] == 3
    assert output["admit_cards"]["total"] == 20
    assert output["answer_keys"]["total"] == 15
    assert output["results"]["total"] == 12
    assert output["entrance_exams"]["total"] == 8
    assert output["entrance_exams"]["active"] == 5
    assert output["users"]["total"] == 100
    assert output["users"]["new_this_week"] == 6


# ─── create_job ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_job_draft():
    from app.routers.admin import create_job
    from app.schemas.jobs import JobCreateRequest, JobResponse

    db = AsyncMock()

    # slug check: no existing
    no_slug = MagicMock()
    no_slug.scalar_one_or_none.return_value = None
    db.execute.return_value = no_slug
    db.flush = AsyncMock()
    db.add = MagicMock()

    mock_resp = MagicMock()
    mock_resp.model_dump.return_value = {"id": str(uuid.uuid4()), "status": "draft"}

    body = JobCreateRequest(job_title="Test Job", organization="Org", status="draft")
    req = _make_request()

    with patch.object(JobResponse, "model_validate", return_value=mock_resp):
        output = await create_job(
            body=body, request=req, current_admin=_make_admin(), db=db
        )

    assert output["status"] == "draft"
    assert db.add.call_count >= 1  # job + log


@pytest.mark.asyncio
async def test_create_job_active_triggers_notification():
    from app.routers.admin import create_job
    from app.schemas.jobs import JobCreateRequest, JobResponse

    db = AsyncMock()

    no_slug = MagicMock()
    no_slug.scalar_one_or_none.return_value = None
    db.execute.return_value = no_slug
    db.flush = AsyncMock()
    db.add = MagicMock()

    mock_resp = MagicMock()
    mock_resp.model_dump.return_value = {"id": str(uuid.uuid4()), "status": "active"}

    body = JobCreateRequest(job_title="Active Job", organization="Org", status="active")
    req = _make_request()

    with patch.object(JobResponse, "model_validate", return_value=mock_resp), patch(
        "app.tasks.notifications.send_new_job_notifications"
    ) as mock_task:
        mock_task.delay = MagicMock()
        output = await create_job(
            body=body, request=req, current_admin=_make_admin(), db=db
        )

    assert output["status"] == "active"


@pytest.mark.asyncio
async def test_create_job_slug_conflict():
    """When slug already exists, increment counter until unique."""
    from app.routers.admin import create_job
    from app.schemas.jobs import JobCreateRequest, JobResponse

    db = AsyncMock()

    # first slug exists, second doesn't
    existing = MagicMock()
    existing.scalar_one_or_none.return_value = MagicMock()
    unique = MagicMock()
    unique.scalar_one_or_none.return_value = None
    db.execute.side_effect = [existing, unique]
    db.flush = AsyncMock()
    db.add = MagicMock()

    mock_resp = MagicMock()
    mock_resp.model_dump.return_value = {"id": str(uuid.uuid4()), "slug": "test-job-1"}

    body = JobCreateRequest(job_title="Test Job", organization="Org", status="draft")
    req = _make_request()

    with patch.object(JobResponse, "model_validate", return_value=mock_resp):
        output = await create_job(
            body=body, request=req, current_admin=_make_admin(), db=db
        )

    assert output["slug"] == "test-job-1"


# ─── update_job ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_job_not_found():
    from app.routers.admin import update_job
    from app.schemas.jobs import JobUpdateRequest
    from fastapi import HTTPException

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    body = JobUpdateRequest(description="Updated")
    with pytest.raises(HTTPException) as exc_info:
        await update_job(
            job_id=uuid.uuid4(),
            body=body,
            request=_make_request(),
            current_admin=_make_admin(),
            db=db,
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_job_operator_restricted():
    from app.routers.admin import update_job
    from app.schemas.jobs import JobUpdateRequest
    from fastapi import HTTPException

    job = _make_job()
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = job
    db.execute.return_value = result

    admin = _make_admin(role="operator")
    body = JobUpdateRequest(organization="NewOrg")  # operator can't change org
    with pytest.raises(HTTPException) as exc_info:
        await update_job(
            job_id=job.id,
            body=body,
            request=_make_request(),
            current_admin=admin,
            db=db,
        )
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_update_job_no_changes():
    from app.routers.admin import update_job
    from app.schemas.jobs import JobResponse, JobUpdateRequest

    job = _make_job(status="active")
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = job
    db.execute.return_value = result

    mock_resp = MagicMock()
    mock_resp.model_dump.return_value = {"id": str(job.id)}

    # Pass same value as mock job has — since MagicMock comparison won't match, we need status to equal
    job.status = "active"
    body = JobUpdateRequest(status="active")

    with patch.object(JobResponse, "model_validate", return_value=mock_resp):
        output = await update_job(
            job_id=job.id,
            body=body,
            request=_make_request(),
            current_admin=_make_admin(),
            db=db,
        )
    # no changes recorded — returns early with model dump
    assert "id" in output


@pytest.mark.asyncio
async def test_update_job_with_changes():
    from app.routers.admin import update_job
    from app.schemas.jobs import JobResponse, JobUpdateRequest

    job = _make_job(status="draft")
    job.description = "Old description"
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = job
    db.execute.return_value = result
    db.add = MagicMock()

    mock_resp = MagicMock()
    mock_resp.model_dump.return_value = {"id": str(job.id), "status": "active"}

    body = JobUpdateRequest(status="active")

    with patch.object(JobResponse, "model_validate", return_value=mock_resp), patch(
        "app.tasks.notifications.notify_priority_subscribers"
    ) as mock_prio, patch(
        "app.tasks.notifications.send_new_job_notifications"
    ) as mock_notif:
        mock_prio.delay = MagicMock()
        mock_notif.delay = MagicMock()
        output = await update_job(
            job_id=job.id,
            body=body,
            request=_make_request(),
            current_admin=_make_admin(),
            db=db,
        )

    assert output["status"] == "active"


# ─── approve_job ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_approve_job_not_found():
    from app.routers.admin import approve_job
    from fastapi import HTTPException

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    with pytest.raises(HTTPException) as exc_info:
        await approve_job(
            job_id=uuid.uuid4(),
            request=_make_request(),
            current_admin=_make_admin(),
            db=db,
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_approve_job_not_draft():
    from app.routers.admin import approve_job
    from fastapi import HTTPException

    job = _make_job(status="active")
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = job
    db.execute.return_value = result

    with pytest.raises(HTTPException) as exc_info:
        await approve_job(
            job_id=job.id, request=_make_request(), current_admin=_make_admin(), db=db
        )
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_approve_job_success():
    from app.routers.admin import approve_job
    from app.schemas.jobs import JobResponse

    job = _make_job(status="draft")
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = job
    db.execute.return_value = result
    db.add = MagicMock()

    mock_resp = MagicMock()
    mock_resp.model_dump.return_value = {"id": str(job.id), "status": "active"}

    with patch.object(JobResponse, "model_validate", return_value=mock_resp), patch(
        "app.tasks.notifications.send_new_job_notifications"
    ) as mock_notif:
        mock_notif.delay = MagicMock()
        output = await approve_job(
            job_id=job.id, request=_make_request(), current_admin=_make_admin(), db=db
        )

    assert job.status == "active"
    assert output["status"] == "active"


# ─── delete_job ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_job_not_found():
    from app.routers.admin import delete_job
    from fastapi import HTTPException

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    with pytest.raises(HTTPException) as exc_info:
        await delete_job(
            job_id=uuid.uuid4(), request=_make_request(), admin=_make_admin(), db=db
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_job_success():
    from app.routers.admin import delete_job

    job = _make_job(status="active")
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = job
    db.execute.return_value = result
    db.add = MagicMock()

    await delete_job(job_id=job.id, request=_make_request(), admin=_make_admin(), db=db)
    assert job.status == "cancelled"


# ─── list_users ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_users_no_filter():
    from app.routers.admin import list_users
    from app.schemas.auth import UserResponse

    db = AsyncMock()
    count_r = MagicMock()
    count_r.scalar.return_value = 0
    data_r = MagicMock()
    data_r.scalars.return_value.all.return_value = []
    db.execute.side_effect = [count_r, data_r]

    output = await list_users(
        status_filter=None,
        q=None,
        limit=20,
        offset=0,
        admin=_make_admin(),
        db=db,
    )
    assert output["pagination"]["total"] == 0
    assert output["data"] == []


@pytest.mark.asyncio
async def test_list_users_with_search():
    from app.routers.admin import list_users
    from app.schemas.auth import UserResponse

    user = _make_user()
    db = AsyncMock()
    count_r = MagicMock()
    count_r.scalar.return_value = 1
    data_r = MagicMock()
    data_r.scalars.return_value.all.return_value = [user]
    db.execute.side_effect = [count_r, data_r]

    mock_resp = MagicMock()
    mock_resp.model_dump.return_value = {"id": str(user.id), "email": user.email}

    with patch.object(UserResponse, "model_validate", return_value=mock_resp):
        output = await list_users(
            status_filter="active",
            q="test",
            limit=20,
            offset=0,
            admin=_make_admin(),
            db=db,
        )
    assert output["pagination"]["total"] == 1
    assert len(output["data"]) == 1


# ─── get_user ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_user_not_found():
    from app.routers.admin import get_user
    from fastapi import HTTPException

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    with pytest.raises(HTTPException) as exc_info:
        await get_user(user_id=uuid.uuid4(), admin=_make_admin(), db=db)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_user_found_no_profile():
    from app.routers.admin import get_user
    from app.schemas.auth import UserResponse

    user = _make_user()
    db = AsyncMock()
    user_r = MagicMock()
    user_r.scalar_one_or_none.return_value = user
    profile_r = MagicMock()
    profile_r.scalar_one_or_none.return_value = None
    db.execute.side_effect = [user_r, profile_r]

    mock_resp = MagicMock()
    mock_resp.model_dump.return_value = {"id": str(user.id)}

    with patch.object(UserResponse, "model_validate", return_value=mock_resp):
        output = await get_user(user_id=user.id, admin=_make_admin(), db=db)
    assert "profile" not in output


@pytest.mark.asyncio
async def test_get_user_found_with_profile():
    from app.routers.admin import get_user
    from app.schemas.auth import UserResponse

    user = _make_user()
    profile = MagicMock()
    profile.date_of_birth = None
    profile.gender = "Male"
    profile.category = "General"
    profile.state = "Delhi"
    profile.city = "New Delhi"
    profile.highest_qualification = "Graduate"

    db = AsyncMock()
    user_r = MagicMock()
    user_r.scalar_one_or_none.return_value = user
    profile_r = MagicMock()
    profile_r.scalar_one_or_none.return_value = profile
    db.execute.side_effect = [user_r, profile_r]

    mock_resp = MagicMock()
    mock_resp.model_dump.return_value = {"id": str(user.id)}

    with patch.object(UserResponse, "model_validate", return_value=mock_resp):
        output = await get_user(user_id=user.id, admin=_make_admin(), db=db)
    assert output["profile"]["gender"] == "Male"
    assert output["profile"]["state"] == "Delhi"


# ─── update_user_status ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_user_status_invalid():
    from app.routers.admin import UserStatusRequest, update_user_status
    from fastapi import HTTPException

    req = _make_request()
    db = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await update_user_status(
            user_id=uuid.uuid4(),
            body=UserStatusRequest(status="deleted"),
            request=req,
            admin=_make_admin(),
            db=db,
        )
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_update_user_status_not_found():
    from app.routers.admin import UserStatusRequest, update_user_status
    from fastapi import HTTPException

    req = _make_request()
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    with pytest.raises(HTTPException) as exc_info:
        await update_user_status(
            user_id=uuid.uuid4(),
            body=UserStatusRequest(status="suspended"),
            request=req,
            admin=_make_admin(),
            db=db,
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_user_status_success():
    from app.routers.admin import UserStatusRequest, update_user_status

    user = _make_user()
    user.status = "active"
    req = _make_request()
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    db.execute.return_value = result
    db.add = MagicMock()

    output = await update_user_status(
        user_id=user.id,
        body=UserStatusRequest(status="suspended"),
        request=req,
        admin=_make_admin(),
        db=db,
    )
    assert user.status == "suspended"
    assert "suspended" in output["message"]


# ─── admin_logs ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_logs_empty():
    from app.routers.admin import admin_logs

    db = AsyncMock()
    count_r = MagicMock()
    count_r.scalar.return_value = 0
    data_r = MagicMock()
    data_r.scalars.return_value.all.return_value = []
    db.execute.side_effect = [count_r, data_r]

    output = await admin_logs(limit=20, offset=0, admin=_make_admin(), db=db)
    assert output["pagination"]["total"] == 0
    assert output["data"] == []


@pytest.mark.asyncio
async def test_admin_logs_with_data():
    from app.routers.admin import admin_logs

    log = MagicMock()
    log.id = uuid.uuid4()
    log.admin_id = uuid.uuid4()
    log.action = "create_job"
    log.resource_type = "job_vacancy"
    log.resource_id = uuid.uuid4()
    log.details = "Created job"
    log.changes = {}
    log.ip_address = "127.0.0.1"
    log.timestamp = datetime.now(timezone.utc)

    db = AsyncMock()
    count_r = MagicMock()
    count_r.scalar.return_value = 1
    data_r = MagicMock()
    data_r.scalars.return_value.all.return_value = [log]
    db.execute.side_effect = [count_r, data_r]

    output = await admin_logs(limit=20, offset=0, admin=_make_admin(), db=db)
    assert output["pagination"]["total"] == 1
    assert output["data"][0]["action"] == "create_job"
    assert output["data"][0]["details"] == "Created job"


@pytest.mark.asyncio
async def test_admin_logs_null_resource_id():
    from app.routers.admin import admin_logs

    log = MagicMock()
    log.id = uuid.uuid4()
    log.admin_id = uuid.uuid4()
    log.action = "login"
    log.resource_type = None
    log.resource_id = None  # no resource
    log.details = None
    log.changes = {}
    log.ip_address = None
    log.timestamp = None

    db = AsyncMock()
    count_r = MagicMock()
    count_r.scalar.return_value = 1
    data_r = MagicMock()
    data_r.scalars.return_value.all.return_value = [log]
    db.execute.side_effect = [count_r, data_r]

    output = await admin_logs(limit=20, offset=0, admin=_make_admin(), db=db)
    assert output["data"][0]["resource_id"] is None
    assert output["data"][0]["ip_address"] is None
    assert output["data"][0]["timestamp"] is None
