"""Unit tests for watch route handlers (watch/unwatch jobs & exams, list watched)."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

# ── fixtures ──────────────────────────────────────────────────────────────────


def _make_user():
    u = MagicMock()
    u.id = uuid.uuid4()
    return u


def _make_job(**kwargs):
    j = MagicMock()
    j.id = uuid.uuid4()
    j.job_title = kwargs.get("job_title", "SSC CGL")
    j.slug = kwargs.get("slug", "ssc-cgl")
    j.organization = kwargs.get("organization", "SSC")
    j.application_end = None
    j.status = "active"
    return j


def _make_admission(**kwargs):
    e = MagicMock()
    e.id = uuid.uuid4()
    e.exam_name = kwargs.get("exam_name", "NEET")
    e.slug = kwargs.get("slug", "neet-2025")
    e.conducting_body = "NTA"
    e.application_end = None
    e.status = "upcoming"
    return e


def _make_watch(entity_type, entity_id):
    w = MagicMock()
    w.id = uuid.uuid4()
    w.entity_type = entity_type
    w.entity_id = entity_id
    w.created_at = datetime.now(timezone.utc)
    return w


def _db_single(obj):
    res = MagicMock()
    res.scalar_one_or_none.return_value = obj
    db = AsyncMock()
    db.execute = AsyncMock(return_value=res)
    return db


# ═══════════════════════════════════════════════════════════════
# watch_job
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_watch_job_job_not_found():
    from app.routers.watches import watch_job
    from fastapi import HTTPException

    user = _make_user()
    db = _db_single(None)
    with pytest.raises(HTTPException) as exc:
        await watch_job(job_id=uuid.uuid4(), current_user=(user, {}), db=db)
    assert exc.value.status_code == 404
    assert "job" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_watch_job_already_watching():
    from app.routers.watches import watch_job

    user = _make_user()
    job = _make_job()
    watch = _make_watch("job", job.id)

    job_res = MagicMock()
    job_res.scalar_one_or_none.return_value = job
    watch_res = MagicMock()
    watch_res.scalar_one_or_none.return_value = watch

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[job_res, watch_res])
    result = await watch_job(job_id=job.id, current_user=(user, {}), db=db)

    assert result["watching"] is True
    assert "already" in result["message"].lower()
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_watch_job_max_watches_exceeded():
    from app.routers.watches import MAX_WATCHES, watch_job
    from fastapi import HTTPException

    user = _make_user()
    job = _make_job()

    job_res = MagicMock()
    job_res.scalar_one_or_none.return_value = job
    no_watch_res = MagicMock()
    no_watch_res.scalar_one_or_none.return_value = None
    count_res = MagicMock()
    count_res.scalar.return_value = MAX_WATCHES

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[job_res, no_watch_res, count_res])
    with pytest.raises(HTTPException) as exc:
        await watch_job(job_id=job.id, current_user=(user, {}), db=db)
    assert exc.value.status_code == 400
    assert str(MAX_WATCHES) in exc.value.detail


@pytest.mark.asyncio
async def test_watch_job_success():
    from app.routers.watches import watch_job

    user = _make_user()
    job = _make_job()

    job_res = MagicMock()
    job_res.scalar_one_or_none.return_value = job
    no_watch_res = MagicMock()
    no_watch_res.scalar_one_or_none.return_value = None
    count_res = MagicMock()
    count_res.scalar.return_value = 5

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[job_res, no_watch_res, count_res])
    result = await watch_job(job_id=job.id, current_user=(user, {}), db=db)

    assert result["watching"] is True
    assert "now watching" in result["message"].lower()
    db.add.assert_called_once()
    db.commit.assert_called_once()


# ═══════════════════════════════════════════════════════════════
# unwatch_job
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_unwatch_job_not_watching():
    from app.routers.watches import unwatch_job
    from fastapi import HTTPException

    user = _make_user()
    db = _db_single(None)
    with pytest.raises(HTTPException) as exc:
        await unwatch_job(job_id=uuid.uuid4(), current_user=(user, {}), db=db)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_unwatch_job_success():
    from app.routers.watches import unwatch_job

    user = _make_user()
    job = _make_job()
    watch = _make_watch("job", job.id)
    db = _db_single(watch)

    result = await unwatch_job(job_id=job.id, current_user=(user, {}), db=db)

    assert result["watching"] is False
    assert "unwatched" in result["message"].lower()
    db.delete.assert_called_once_with(watch)
    db.commit.assert_called_once()


# ═══════════════════════════════════════════════════════════════
# watch_exam
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_watch_exam_not_found():
    from app.routers.watches import watch_exam
    from fastapi import HTTPException

    user = _make_user()
    db = _db_single(None)
    with pytest.raises(HTTPException) as exc:
        await watch_admission(admission_id=uuid.uuid4(), current_user=(user, {}), db=db)
    assert exc.value.status_code == 404
    assert "exam" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_watch_exam_already_watching():
    from app.routers.watches import watch_exam

    user = _make_user()
    admission = _make_admission()
    watch = _make_watch("exam", exam.id)

    exam_res = MagicMock()
    exam_res.scalar_one_or_none.return_value = admission
    watch_res = MagicMock()
    watch_res.scalar_one_or_none.return_value = watch

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[exam_res, watch_res])
    result = await watch_admission(
        admission_id=admission.id, current_user=(user, {}), db=db
    )

    assert result["watching"] is True
    assert "already" in result["message"].lower()
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_watch_exam_max_watches_exceeded():
    from app.routers.watches import MAX_WATCHES, watch_exam
    from fastapi import HTTPException

    user = _make_user()
    admission = _make_admission()

    exam_res = MagicMock()
    exam_res.scalar_one_or_none.return_value = admission
    no_watch_res = MagicMock()
    no_watch_res.scalar_one_or_none.return_value = None
    count_res = MagicMock()
    count_res.scalar.return_value = MAX_WATCHES

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[exam_res, no_watch_res, count_res])
    with pytest.raises(HTTPException) as exc:
        await watch_admission(admission_id=admission.id, current_user=(user, {}), db=db)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_watch_exam_success():
    from app.routers.watches import watch_exam

    user = _make_user()
    admission = _make_admission()

    exam_res = MagicMock()
    exam_res.scalar_one_or_none.return_value = admission
    no_watch_res = MagicMock()
    no_watch_res.scalar_one_or_none.return_value = None
    count_res = MagicMock()
    count_res.scalar.return_value = 0

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[exam_res, no_watch_res, count_res])
    result = await watch_admission(
        admission_id=admission.id, current_user=(user, {}), db=db
    )

    assert result["watching"] is True
    db.add.assert_called_once()
    db.commit.assert_called_once()


# ═══════════════════════════════════════════════════════════════
# unwatch_exam
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_unwatch_exam_not_watching():
    from app.routers.watches import unwatch_exam
    from fastapi import HTTPException

    user = _make_user()
    db = _db_single(None)
    with pytest.raises(HTTPException) as exc:
        await unwatch_admission(
            admission_id=uuid.uuid4(), current_user=(user, {}), db=db
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_unwatch_exam_success():
    from app.routers.watches import unwatch_exam

    user = _make_user()
    admission = _make_admission()
    watch = _make_watch("exam", exam.id)
    db = _db_single(watch)

    result = await unwatch_admission(
        admission_id=admission.id, current_user=(user, {}), db=db
    )

    assert result["watching"] is False
    db.delete.assert_called_once_with(watch)
    db.commit.assert_called_once()


# ═══════════════════════════════════════════════════════════════
# list_watched
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_list_watched_empty():
    from app.routers.watches import list_watched

    user = _make_user()
    watches_res = MagicMock()
    watches_res.scalars.return_value.all.return_value = []
    db = AsyncMock()
    db.execute = AsyncMock(return_value=watches_res)

    result = await list_watched(current_user=(user, {}), db=db)
    assert result["jobs"] == []
    assert result["exams"] == []
    assert result["total"] == 0


@pytest.mark.asyncio
async def test_list_watched_with_job():
    from app.routers.watches import list_watched

    user = _make_user()
    job = _make_job()
    watch = _make_watch("job", job.id)

    watches_res = MagicMock()
    watches_res.scalars.return_value.all.return_value = [watch]
    jobs_res = MagicMock()
    jobs_res.scalars.return_value.all.return_value = [job]

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[watches_res, jobs_res])

    result = await list_watched(current_user=(user, {}), db=db)
    assert len(result["jobs"]) == 1
    assert result["jobs"][0]["slug"] == "ssc-cgl"
    assert result["exams"] == []
    assert result["total"] == 1


@pytest.mark.asyncio
async def test_list_watched_with_exam():
    from app.routers.watches import list_watched

    user = _make_user()
    admission = _make_admission()
    watch = _make_watch("exam", exam.id)

    watches_res = MagicMock()
    watches_res.scalars.return_value.all.return_value = [watch]
    exams_res = MagicMock()
    exams_res.scalars.return_value.all.return_value = [admission]

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[watches_res, exams_res])

    result = await list_watched(current_user=(user, {}), db=db)
    assert len(result["exams"]) == 1
    assert result["exams"][0]["slug"] == "neet-2025"
    assert result["jobs"] == []
    assert result["total"] == 1


@pytest.mark.asyncio
async def test_list_watched_mixed_jobs_and_exams():
    from app.routers.watches import list_watched

    user = _make_user()
    job = _make_job()
    admission = _make_admission()
    job_watch = _make_watch("job", job.id)
    exam_watch = _make_watch("exam", exam.id)

    watches_res = MagicMock()
    watches_res.scalars.return_value.all.return_value = [job_watch, exam_watch]
    jobs_res = MagicMock()
    jobs_res.scalars.return_value.all.return_value = [job]
    exams_res = MagicMock()
    exams_res.scalars.return_value.all.return_value = [admission]

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[watches_res, jobs_res, exams_res])

    result = await list_watched(current_user=(user, {}), db=db)
    assert len(result["jobs"]) == 1
    assert len(result["exams"]) == 1
    assert result["total"] == 2
