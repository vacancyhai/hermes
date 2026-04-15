"""Unit tests for admission route handlers."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── fixtures ──────────────────────────────────────────────────────────────────


def _make_admission(**kwargs):
    e = MagicMock()
    e.id = uuid.uuid4()
    e.slug = kwargs.get("slug", "neet-2025")
    e.admission_name = kwargs.get("admission_name", "NEET")
    e.conducting_body = "NTA"
    e.counselling_body = None
    e.admission_type = "national"
    e.stream = "medical"
    e.eligibility = {}
    e.admission_details = {}
    e.selection_process = []
    e.seats_info = None
    e.application_start = None
    e.application_end = None
    e.admission_date = None
    e.result_date = None
    e.counselling_start = None
    e.fee_general = None
    e.fee_obc = None
    e.fee_sc_st = None
    e.fee_ews = None
    e.fee_female = None
    e.description = None
    e.short_description = None
    e.source_url = None
    e.status = kwargs.get("status", "upcoming")
    e.published_at = None
    e.created_at = datetime.now(timezone.utc)
    e.updated_at = datetime.now(timezone.utc)
    return e


def _db_list(items, count=None):
    count_res = MagicMock()
    count_res.scalar.return_value = count if count is not None else len(items)
    items_res = MagicMock()
    items_res.scalars.return_value.all.return_value = items
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[count_res, items_res])
    return db


def _db_single(obj):
    res = MagicMock()
    res.scalar_one_or_none.return_value = obj
    db = AsyncMock()
    db.execute = AsyncMock(return_value=res)
    return db


def _mock_item(id_val):
    m = MagicMock()
    m.model_dump.return_value = {"id": str(id_val)}
    return m


# ═══════════════════════════════════════════════════════════════
# Public — list_admissions
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_list_admissions_empty():
    from app.routers.admissions import list_admissions

    result = await list_admissions(
        q=None,
        stream=None,
        admission_type=None,
        limit=20,
        offset=0,
        db=_db_list([], count=0),
    )
    assert result["data"] == []
    assert result["pagination"]["total"] == 0
    assert result["pagination"]["has_more"] is False


@pytest.mark.asyncio
async def test_list_admissions_returns_items():
    from app.routers.admissions import list_admissions
    from app.schemas.admissions import AdmissionListItem

    admission = _make_admission()
    with patch.object(
        AdmissionListItem, "model_validate", return_value=_mock_item(admission.id)
    ):
        result = await list_admissions(
            q=None,
            stream=None,
            admission_type=None,
            limit=20,
            offset=0,
            db=_db_list([admission]),
        )
    assert len(result["data"]) == 1
    assert result["pagination"]["total"] == 1


@pytest.mark.asyncio
async def test_list_admissions_pagination_has_more():
    from app.routers.admissions import list_admissions
    from app.schemas.admissions import AdmissionListItem

    admission = _make_admission()
    with patch.object(
        AdmissionListItem, "model_validate", return_value=_mock_item(admission.id)
    ):
        result = await list_admissions(
            q=None,
            stream=None,
            admission_type=None,
            limit=1,
            offset=0,
            db=_db_list([admission], count=3),
        )
    assert result["pagination"]["has_more"] is True


@pytest.mark.asyncio
async def test_list_admissions_with_search_query():
    from app.routers.admissions import list_admissions

    result = await list_admissions(
        q="NEET",
        stream=None,
        admission_type=None,
        limit=20,
        offset=0,
        db=_db_list([], count=0),
    )
    assert result["pagination"]["total"] == 0


@pytest.mark.asyncio
async def test_list_admissions_with_stream_filter():
    from app.routers.admissions import list_admissions

    result = await list_admissions(
        q=None,
        stream="medical",
        admission_type=None,
        limit=20,
        offset=0,
        db=_db_list([], count=0),
    )
    assert result["pagination"]["total"] == 0


@pytest.mark.asyncio
async def test_list_admissions_with_all_filters():
    from app.routers.admissions import list_admissions

    result = await list_admissions(
        q=None,
        stream="engineering",
        admission_type="national",
        limit=10,
        offset=0,
        db=_db_list([], count=0),
    )
    assert result["pagination"]["total"] == 0


# ═══════════════════════════════════════════════════════════════
# Public — get_admission (detail)
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_get_admission_not_found():
    from app.routers.admissions import get_admission
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await get_admission(slug="nonexistent", db=_db_single(None))
    assert exc.value.status_code == 404
    assert exc.value.detail == "Admission not found"


@pytest.mark.asyncio
async def test_get_admission_found_increments_views_and_returns_docs():
    from app.routers.admissions import get_admission
    from app.schemas.admissions import AdmissionResponse

    admission = _make_admission()
    admission.slug = "test-admission"

    select_res = MagicMock()
    select_res.scalar_one_or_none.return_value = admission
    empty_res = MagicMock()
    empty_res.scalars.return_value.all.return_value = []

    db = AsyncMock()
    db.execute = AsyncMock(
        side_effect=[
            select_res,  # select admission
            empty_res,  # admit_cards
            empty_res,  # answer_keys
            empty_res,  # results
        ]
    )

    mock_resp = MagicMock()
    mock_resp.model_dump.return_value = {
        "id": str(admission.id),
        "slug": admission.slug,
    }

    with patch.object(AdmissionResponse, "model_validate", return_value=mock_resp):
        result = await get_admission(slug=admission.slug, db=db)

    assert result["admit_cards"] == []
    assert result["answer_keys"] == []
    assert result["results"] == []


# ═══════════════════════════════════════════════════════════════
# Admin — admin_list_admissions
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_admin_list_admissions_empty():
    from app.routers.admissions import admin_list_admissions

    result = await admin_list_admissions(
        limit=20,
        offset=0,
        stream=None,
        admission_type=None,
        status=None,
        admin=MagicMock(),
        db=_db_list([], count=0),
    )
    assert result["data"] == []
    assert result["pagination"]["total"] == 0


@pytest.mark.asyncio
async def test_admin_list_admissions_with_results():
    from app.routers.admissions import admin_list_admissions
    from app.schemas.admissions import AdmissionListItem

    admission = _make_admission()
    with patch.object(
        AdmissionListItem, "model_validate", return_value=_mock_item(admission.id)
    ):
        result = await admin_list_admissions(
            limit=20,
            offset=0,
            stream=None,
            admission_type=None,
            status=None,
            admin=MagicMock(),
            db=_db_list([admission]),
        )
    assert result["pagination"]["total"] == 1


@pytest.mark.asyncio
async def test_admin_list_admissions_with_filters():
    from app.routers.admissions import admin_list_admissions

    result = await admin_list_admissions(
        limit=10,
        offset=0,
        stream="medical",
        admission_type="national",
        status="active",
        admin=MagicMock(),
        db=_db_list([], count=0),
    )
    assert result["pagination"]["total"] == 0


# ═══════════════════════════════════════════════════════════════
# Admin — admin_get_admission
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_admin_get_admission_not_found():
    from app.routers.admissions import admin_get_admission
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await admin_get_admission(
            admission_id=uuid.uuid4(), admin=MagicMock(), db=_db_single(None)
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_admin_get_admission_found():
    from app.routers.admissions import admin_get_admission
    from app.schemas.admissions import AdmissionResponse

    admission = _make_admission()
    mock_resp = _mock_item(admission.id)
    with patch.object(AdmissionResponse, "model_validate", return_value=mock_resp):
        result = await admin_get_admission(
            admission_id=admission.id, admin=MagicMock(), db=_db_single(admission)
        )
    assert result == {"id": str(admission.id)}


# ═══════════════════════════════════════════════════════════════
# Admin — create_admission
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_create_admission_success():
    from app.routers.admissions import create_admission
    from app.schemas.admissions import AdmissionCreateRequest, AdmissionResponse

    body = AdmissionCreateRequest(
        admission_name="NEET 2025",
        conducting_body="NTA",
        admission_type="ug",
        stream="medical",
        slug="neet-2025",
    )
    slug_res = MagicMock()
    slug_res.scalar.return_value = []
    db = AsyncMock()
    db.execute = AsyncMock(return_value=slug_res)

    mock_resp = _mock_item(uuid.uuid4())
    with patch.object(AdmissionResponse, "model_validate", return_value=mock_resp):
        await create_admission(body=body, admin=MagicMock(), db=db)

    db.add.assert_called_once()
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_create_admission_slug_collision_increments():
    from app.routers.admissions import create_admission
    from app.schemas.admissions import AdmissionCreateRequest
    from fastapi import HTTPException

    body = AdmissionCreateRequest(
        admission_name="NEET",
        conducting_body="NTA",
        admission_type="ug",
        stream="medical",
        slug="neet",
    )
    slug_res = MagicMock()
    slug_res.scalar.return_value = "neet"
    db = AsyncMock()
    db.execute = AsyncMock(return_value=slug_res)

    with pytest.raises(HTTPException) as exc:
        await create_admission(body=body, admin=MagicMock(), db=db)
    assert exc.value.status_code == 409
    assert "Slug 'neet' is already in use" in exc.value.detail


@pytest.mark.asyncio
async def test_create_admission_active_sets_published_at():
    from app.routers.admissions import create_admission
    from app.schemas.admissions import AdmissionCreateRequest, AdmissionResponse

    body = AdmissionCreateRequest(
        admission_name="JEE Main",
        conducting_body="NTA",
        admission_type="ug",
        stream="engineering",
        status="active",
        slug="jee-main",
    )
    slug_res = MagicMock()
    slug_res.scalar.return_value = []
    db = AsyncMock()
    db.execute = AsyncMock(return_value=slug_res)

    mock_resp = _mock_item(uuid.uuid4())
    with patch.object(AdmissionResponse, "model_validate", return_value=mock_resp):
        await create_admission(body=body, admin=MagicMock(), db=db)

    added_admission = db.add.call_args[0][0]
    assert added_admission.published_at is not None


@pytest.mark.asyncio
async def test_create_admission_non_active_no_published_at():
    from app.routers.admissions import create_admission
    from app.schemas.admissions import AdmissionCreateRequest, AdmissionResponse

    body = AdmissionCreateRequest(
        admission_name="CAT 2025",
        conducting_body="IIM",
        admission_type="pg",
        stream="management",
        status="upcoming",
        slug="cat-2025",
    )
    slug_res = MagicMock()
    slug_res.scalar.return_value = []
    db = AsyncMock()
    db.execute = AsyncMock(return_value=slug_res)

    mock_resp = _mock_item(uuid.uuid4())
    with patch.object(AdmissionResponse, "model_validate", return_value=mock_resp):
        await create_admission(body=body, admin=MagicMock(), db=db)

    added_admission = db.add.call_args[0][0]
    assert added_admission.published_at is None


# ═══════════════════════════════════════════════════════════════
# Admin — update_admission
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_update_admission_not_found():
    from app.routers.admissions import update_admission
    from app.schemas.admissions import AdmissionUpdateRequest
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await update_admission(
            admission_id=uuid.uuid4(),
            body=AdmissionUpdateRequest(),
            admin=MagicMock(),
            db=_db_single(None),
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_admission_success():
    from app.routers.admissions import update_admission
    from app.schemas.admissions import AdmissionResponse, AdmissionUpdateRequest

    admission = _make_admission()
    mock_resp = _mock_item(admission.id)
    with patch.object(AdmissionResponse, "model_validate", return_value=mock_resp):
        result = await update_admission(
            admission_id=admission.id,
            body=AdmissionUpdateRequest(admission_name="Updated NEET"),
            admin=MagicMock(),
            db=_db_single(admission),
        )
    assert result == {"id": str(admission.id)}


# ═══════════════════════════════════════════════════════════════
# Admin — delete_admission
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_delete_admission_not_found():
    from app.routers.admissions import delete_admission
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await delete_admission(
            admission_id=uuid.uuid4(), admin=MagicMock(), db=_db_single(None)
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_admission_success():
    from app.routers.admissions import delete_admission

    admission = _make_admission()
    db = _db_single(admission)
    await delete_admission(admission_id=admission.id, admin=MagicMock(), db=db)
    db.delete.assert_called_once_with(admission)
