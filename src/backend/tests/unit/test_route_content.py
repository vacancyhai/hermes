"""Unit tests for content route handlers (admit cards, answer keys, results)."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── fixtures ─────────────────────────────────────────────────────────────────


def _make_card(**kwargs):
    c = MagicMock()
    c.id = uuid.uuid4()
    c.job_id = kwargs.get("job_id", None)
    c.admission_id = kwargs.get("admission_id", None)
    c.phase_number = None
    c.title = "Test Admit Card"
    c.download_url = "https://example.com/card.pdf"
    c.valid_from = None
    c.valid_until = None
    c.notes = None
    c.published_at = None
    c.created_at = datetime.now(timezone.utc)
    c.updated_at = datetime.now(timezone.utc)
    c.job = None
    c.admission = None
    return c


def _make_key(**kwargs):
    k = MagicMock()
    k.id = uuid.uuid4()
    k.job_id = kwargs.get("job_id", None)
    k.admission_id = kwargs.get("admission_id", None)
    k.phase_number = None
    k.title = "Test Answer Key"
    k.answer_key_type = "provisional"
    k.files = []
    k.objection_url = None
    k.objection_deadline = None
    k.published_at = None
    k.created_at = datetime.now(timezone.utc)
    k.updated_at = datetime.now(timezone.utc)
    k.job = None
    k.admission = None
    return k


def _make_result(**kwargs):
    r = MagicMock()
    r.id = uuid.uuid4()
    r.job_id = kwargs.get("job_id", None)
    r.admission_id = kwargs.get("admission_id", None)
    r.phase_number = None
    r.title = "Test Result"
    r.result_type = "final"
    r.download_url = None
    r.cutoff_marks = None
    r.total_qualified = None
    r.notes = None
    r.published_at = None
    r.created_at = datetime.now(timezone.utc)
    r.updated_at = datetime.now(timezone.utc)
    r.job = None
    r.admission = None
    return r


def _db_list(items, count=None):
    """Mock db for list endpoints: first execute returns count, second returns items."""
    count_res = MagicMock()
    count_res.scalar.return_value = count if count is not None else len(items)
    items_res = MagicMock()
    items_res.scalars.return_value.all.return_value = items
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[count_res, items_res])
    return db


def _db_single(obj):
    """Mock db for single-item endpoints."""
    res = MagicMock()
    res.scalar_one_or_none.return_value = obj
    db = AsyncMock()
    db.execute = AsyncMock(return_value=res)
    return db


def _mock_resp(id_val):
    m = MagicMock()
    m.model_dump.return_value = {"id": str(id_val)}
    return m


# ═══════════════════════════════════════════════════════════════
# _validate_document_parent
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_validate_parent_both_ids_raises_400():
    from app.routers.content import _validate_document_parent
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await _validate_document_parent(uuid.uuid4(), uuid.uuid4(), AsyncMock())
    assert exc.value.status_code == 400
    assert "both" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_validate_parent_neither_id_raises_400():
    from app.routers.content import _validate_document_parent
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await _validate_document_parent(None, None, AsyncMock())
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_validate_parent_job_not_found_raises_404():
    from app.routers.content import _validate_document_parent
    from fastapi import HTTPException

    db = _db_single(None)
    db.execute.return_value.scalar.return_value = None
    with pytest.raises(HTTPException) as exc:
        await _validate_document_parent(uuid.uuid4(), None, db)
    assert exc.value.status_code == 404
    assert "job" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_validate_parent_admission_not_found_raises_404():
    from app.routers.content import _validate_document_parent
    from fastapi import HTTPException

    db = _db_single(None)
    db.execute.return_value.scalar.return_value = None
    with pytest.raises(HTTPException) as exc:
        await _validate_document_parent(None, uuid.uuid4(), db)
    assert exc.value.status_code == 404
    assert "admission" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_validate_parent_job_found_passes():
    from app.routers.content import _validate_document_parent

    job_id = uuid.uuid4()
    db = AsyncMock()
    res = MagicMock()
    res.scalar.return_value = job_id
    db.execute = AsyncMock(return_value=res)
    await _validate_document_parent(job_id, None, db)


@pytest.mark.asyncio
async def test_validate_parent_admission_found_passes():
    from app.routers.content import _validate_document_parent

    admission_id = uuid.uuid4()
    db = AsyncMock()
    res = MagicMock()
    res.scalar.return_value = admission_id
    db.execute = AsyncMock(return_value=res)
    await _validate_document_parent(None, admission_id, db)


# ═══════════════════════════════════════════════════════════════
# Admit Cards — Public
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_list_admit_cards_empty():
    from app.routers.content import list_admit_cards

    result = await list_admit_cards(limit=20, offset=0, db=_db_list([], count=0))
    assert result["data"] == []
    assert result["pagination"]["total"] == 0
    assert result["pagination"]["has_more"] is False


@pytest.mark.asyncio
async def test_list_admit_cards_returns_items():
    from app.routers.content import list_admit_cards
    from app.schemas.jobs import AdmitCardResponse

    card = _make_card()
    mock_r = _mock_resp(card.id)
    with patch.object(AdmitCardResponse, "model_validate", return_value=mock_r):
        result = await list_admit_cards(limit=20, offset=0, db=_db_list([card]))
    assert len(result["data"]) == 1
    assert result["pagination"]["total"] == 1


@pytest.mark.asyncio
async def test_list_admit_cards_has_more():
    from app.routers.content import list_admit_cards
    from app.schemas.jobs import AdmitCardResponse

    card = _make_card()
    with patch.object(
        AdmitCardResponse, "model_validate", return_value=_mock_resp(card.id)
    ):
        result = await list_admit_cards(limit=1, offset=0, db=_db_list([card], count=5))
    assert result["pagination"]["has_more"] is True


@pytest.mark.asyncio
async def test_get_admit_card_not_found():
    from app.routers.content import get_admit_card
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await get_admit_card(slug="nonexistent", db=_db_single(None))
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_admit_card_found_no_parent():
    from app.routers.content import get_admit_card
    from app.schemas.jobs import AdmitCardResponse

    card = _make_card()
    card.slug = "test-card"
    mock_r = _mock_resp(card.id)
    with patch.object(AdmitCardResponse, "model_validate", return_value=mock_r):
        result = await get_admit_card(slug=card.slug, db=_db_single(card))
    assert result["id"] == str(card.id)
    assert "job" not in result
    assert "admission" not in result


@pytest.mark.asyncio
async def test_get_admit_card_found_with_job():
    from app.routers.content import get_admit_card
    from app.schemas.jobs import AdmitCardResponse

    job_id = uuid.uuid4()
    card = _make_card(job_id=job_id)
    card.slug = "test-card"
    card.job = MagicMock()
    card.job.id = job_id
    card.job.slug = "ssc-cgl"
    card.job.job_title = "SSC CGL"
    card.job.organization = "SSC"
    mock_r = _mock_resp(card.id)
    with patch.object(AdmitCardResponse, "model_validate", return_value=mock_r):
        result = await get_admit_card(slug=card.slug, db=_db_single(card))
    assert result["job"]["slug"] == "ssc-cgl"


@pytest.mark.asyncio
async def test_get_admit_card_found_with_admission():
    from app.routers.content import get_admit_card
    from app.schemas.jobs import AdmitCardResponse

    admission_id = uuid.uuid4()
    card = _make_card(admission_id=admission_id)
    card.slug = "test-card"
    card.admission = MagicMock()
    card.admission.id = admission_id
    card.admission.slug = "neet-2025"
    card.admission.admission_name = "NEET"
    card.admission.conducting_body = "NTA"
    mock_r = _mock_resp(card.id)
    with patch.object(AdmitCardResponse, "model_validate", return_value=mock_r):
        result = await get_admit_card(slug=card.slug, db=_db_single(card))
    assert result["admission"]["slug"] == "neet-2025"


# ═══════════════════════════════════════════════════════════════
# Admit Cards — Admin
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_admin_list_admit_cards():
    from app.routers.content import admin_list_admit_cards
    from app.schemas.jobs import AdmitCardResponse

    card = _make_card()
    with patch.object(
        AdmitCardResponse, "model_validate", return_value=_mock_resp(card.id)
    ):
        result = await admin_list_admit_cards(
            limit=20, offset=0, db=_db_list([card]), admin=MagicMock()
        )
    assert result["pagination"]["total"] == 1


@pytest.mark.asyncio
async def test_admin_create_admit_card_both_parents_raises():
    from app.routers.content import admin_create_admit_card
    from app.schemas.jobs import AdmitCardCreateRequest
    from fastapi import HTTPException

    body = AdmitCardCreateRequest(
        job_id=uuid.uuid4(),
        admission_id=uuid.uuid4(),
        title="Card",
        slug="test-card",
        download_url="https://x.com/c.pdf",
    )
    with pytest.raises(HTTPException) as exc:
        await admin_create_admit_card(body=body, admin=MagicMock(), db=AsyncMock())
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_admin_create_admit_card_no_parent_raises():
    from app.routers.content import admin_create_admit_card
    from app.schemas.jobs import AdmitCardCreateRequest
    from fastapi import HTTPException

    body = AdmitCardCreateRequest(
        title="Card", slug="test-card", download_url="https://x.com/c.pdf"
    )
    with pytest.raises(HTTPException) as exc:
        await admin_create_admit_card(body=body, admin=MagicMock(), db=AsyncMock())
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_admin_create_admit_card_success():
    from app.routers.content import admin_create_admit_card
    from app.schemas.jobs import AdmitCardCreateRequest, AdmitCardResponse

    job_id = uuid.uuid4()
    body = AdmitCardCreateRequest(
        job_id=job_id,
        title="Card",
        slug="test-card",
        download_url="https://x.com/c.pdf",
    )
    db = AsyncMock()
    parent_res = MagicMock()
    parent_res.scalar.return_value = job_id
    slug_res = MagicMock()
    slug_res.scalar.return_value = None
    db.execute = AsyncMock(side_effect=[parent_res, slug_res])
    with patch.object(
        AdmitCardResponse, "model_validate", return_value=_mock_resp(uuid.uuid4())
    ):
        await admin_create_admit_card(body=body, admin=MagicMock(), db=db)
    db.add.assert_called_once()
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_admin_update_admit_card_not_found():
    from app.routers.content import admin_update_admit_card
    from app.schemas.jobs import AdmitCardUpdateRequest
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await admin_update_admit_card(
            card_id=uuid.uuid4(),
            body=AdmitCardUpdateRequest(),
            admin=MagicMock(),
            db=_db_single(None),
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_admin_update_admit_card_success():
    from app.routers.content import admin_update_admit_card
    from app.schemas.jobs import AdmitCardResponse, AdmitCardUpdateRequest

    card = _make_card()
    with patch.object(
        AdmitCardResponse, "model_validate", return_value=_mock_resp(card.id)
    ):
        await admin_update_admit_card(
            card_id=card.id,
            body=AdmitCardUpdateRequest(title="New Title"),
            admin=MagicMock(),
            db=_db_single(card),
        )
    _db_single(card).flush.assert_not_called()


@pytest.mark.asyncio
async def test_admin_delete_admit_card_not_found():
    from app.routers.content import admin_delete_admit_card
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await admin_delete_admit_card(
            card_id=uuid.uuid4(), admin=MagicMock(), db=_db_single(None)
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_admin_delete_admit_card_success():
    from app.routers.content import admin_delete_admit_card

    card = _make_card()
    db = _db_single(card)
    await admin_delete_admit_card(card_id=card.id, admin=MagicMock(), db=db)
    db.delete.assert_called_once_with(card)


# ═══════════════════════════════════════════════════════════════
# Answer Keys — Public
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_list_answer_keys_empty():
    from app.routers.content import list_answer_keys

    result = await list_answer_keys(limit=20, offset=0, db=_db_list([], count=0))
    assert result["data"] == []
    assert result["pagination"]["total"] == 0


@pytest.mark.asyncio
async def test_list_answer_keys_returns_items():
    from app.routers.content import list_answer_keys
    from app.schemas.jobs import AnswerKeyResponse

    key = _make_key()
    with patch.object(
        AnswerKeyResponse, "model_validate", return_value=_mock_resp(key.id)
    ):
        result = await list_answer_keys(limit=20, offset=0, db=_db_list([key]))
    assert len(result["data"]) == 1


@pytest.mark.asyncio
async def test_get_answer_key_not_found():
    from app.routers.content import get_answer_key
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await get_answer_key(slug="nonexistent", db=_db_single(None))
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_answer_key_found_with_job():
    from app.routers.content import get_answer_key
    from app.schemas.jobs import AnswerKeyResponse

    job_id = uuid.uuid4()
    key = _make_key(job_id=job_id)
    key.slug = "test-key"
    key.job = MagicMock()
    key.job.id = job_id
    key.job.slug = "upsc-2025"
    key.job.job_title = "UPSC"
    key.job.organization = "UPSC"
    mock_r = _mock_resp(key.id)
    with patch.object(AnswerKeyResponse, "model_validate", return_value=mock_r):
        result = await get_answer_key(slug=key.slug, db=_db_single(key))
    assert result["job"]["slug"] == "upsc-2025"


@pytest.mark.asyncio
async def test_get_answer_key_found_with_admission():
    from app.routers.content import get_answer_key
    from app.schemas.jobs import AnswerKeyResponse

    admission_id = uuid.uuid4()
    key = _make_key(admission_id=admission_id)
    key.slug = "test-key"
    key.admission = MagicMock()
    key.admission.id = admission_id
    key.admission.slug = "jee-2025"
    key.admission.admission_name = "JEE"
    key.admission.conducting_body = "NTA"
    mock_r = _mock_resp(key.id)
    with patch.object(AnswerKeyResponse, "model_validate", return_value=mock_r):
        result = await get_answer_key(slug=key.slug, db=_db_single(key))
    assert result["admission"]["slug"] == "jee-2025"


# ═══════════════════════════════════════════════════════════════
# Answer Keys — Admin
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_admin_list_answer_keys():
    from app.routers.content import admin_list_answer_keys
    from app.schemas.jobs import AnswerKeyResponse

    key = _make_key()
    with patch.object(
        AnswerKeyResponse, "model_validate", return_value=_mock_resp(key.id)
    ):
        result = await admin_list_answer_keys(
            limit=20, offset=0, db=_db_list([key]), admin=MagicMock()
        )
    assert result["pagination"]["total"] == 1


@pytest.mark.asyncio
async def test_admin_create_answer_key_success():
    from app.routers.content import admin_create_answer_key
    from app.schemas.jobs import AnswerKeyCreateRequest, AnswerKeyResponse

    job_id = uuid.uuid4()
    body = AnswerKeyCreateRequest(
        job_id=job_id, title="Key", slug="test-key", answer_key_type="provisional"
    )
    db = AsyncMock()
    parent_res = MagicMock()
    parent_res.scalar.return_value = job_id
    slug_res = MagicMock()
    slug_res.scalar.return_value = None
    db.execute = AsyncMock(side_effect=[parent_res, slug_res])
    with patch.object(
        AnswerKeyResponse, "model_validate", return_value=_mock_resp(uuid.uuid4())
    ):
        await admin_create_answer_key(body=body, admin=MagicMock(), db=db)
    db.add.assert_called_once()
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_admin_update_answer_key_not_found():
    from app.routers.content import admin_update_answer_key
    from app.schemas.jobs import AnswerKeyUpdateRequest
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await admin_update_answer_key(
            key_id=uuid.uuid4(),
            body=AnswerKeyUpdateRequest(),
            admin=MagicMock(),
            db=_db_single(None),
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_admin_update_answer_key_success():
    from app.routers.content import admin_update_answer_key
    from app.schemas.jobs import AnswerKeyResponse, AnswerKeyUpdateRequest

    key = _make_key()
    with patch.object(
        AnswerKeyResponse, "model_validate", return_value=_mock_resp(key.id)
    ):
        await admin_update_answer_key(
            key_id=key.id,
            body=AnswerKeyUpdateRequest(title="Updated"),
            admin=MagicMock(),
            db=_db_single(key),
        )


@pytest.mark.asyncio
async def test_admin_delete_answer_key_not_found():
    from app.routers.content import admin_delete_answer_key
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await admin_delete_answer_key(
            key_id=uuid.uuid4(), admin=MagicMock(), db=_db_single(None)
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_admin_delete_answer_key_success():
    from app.routers.content import admin_delete_answer_key

    key = _make_key()
    db = _db_single(key)
    await admin_delete_answer_key(key_id=key.id, admin=MagicMock(), db=db)
    db.delete.assert_called_once_with(key)


# ═══════════════════════════════════════════════════════════════
# Results — Public
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_list_results_empty():
    from app.routers.content import list_results

    result = await list_results(limit=20, offset=0, db=_db_list([], count=0))
    assert result["data"] == []
    assert result["pagination"]["total"] == 0


@pytest.mark.asyncio
async def test_list_results_returns_items():
    from app.routers.content import list_results
    from app.schemas.jobs import ResultResponse

    res_obj = _make_result()
    with patch.object(
        ResultResponse, "model_validate", return_value=_mock_resp(res_obj.id)
    ):
        result = await list_results(limit=20, offset=0, db=_db_list([res_obj]))
    assert len(result["data"]) == 1


@pytest.mark.asyncio
async def test_get_result_not_found():
    from app.routers.content import get_result
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await get_result(slug="nonexistent", db=_db_single(None))
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_result_found_no_parent():
    from app.routers.content import get_result
    from app.schemas.jobs import ResultResponse

    res_obj = _make_result()
    res_obj.slug = "test-result"
    mock_r = _mock_resp(res_obj.id)
    with patch.object(ResultResponse, "model_validate", return_value=mock_r):
        result = await get_result(slug=res_obj.slug, db=_db_single(res_obj))
    assert result["id"] == str(res_obj.id)


@pytest.mark.asyncio
async def test_get_result_found_with_job():
    from app.routers.content import get_result
    from app.schemas.jobs import ResultResponse

    job_id = uuid.uuid4()
    res_obj = _make_result(job_id=job_id)
    res_obj.slug = "test-result"
    res_obj.job = MagicMock()
    res_obj.job.id = job_id
    res_obj.job.slug = "ibps-po"
    res_obj.job.job_title = "IBPS PO"
    res_obj.job.organization = "IBPS"
    mock_r = _mock_resp(res_obj.id)
    with patch.object(ResultResponse, "model_validate", return_value=mock_r):
        result = await get_result(slug=res_obj.slug, db=_db_single(res_obj))
    assert result["job"]["slug"] == "ibps-po"


@pytest.mark.asyncio
async def test_get_result_found_with_admission():
    from app.routers.content import get_result
    from app.schemas.jobs import ResultResponse

    admission_id = uuid.uuid4()
    res_obj = _make_result(admission_id=admission_id)
    res_obj.slug = "test-result"
    res_obj.admission = MagicMock()
    res_obj.admission.id = admission_id
    res_obj.admission.slug = "clat-2025"
    res_obj.admission.admission_name = "CLAT"
    res_obj.admission.conducting_body = "NLU"
    mock_r = _mock_resp(res_obj.id)
    with patch.object(ResultResponse, "model_validate", return_value=mock_r):
        result = await get_result(slug=res_obj.slug, db=_db_single(res_obj))
    assert result["admission"]["slug"] == "clat-2025"


# ═══════════════════════════════════════════════════════════════
# Results — Admin
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_admin_list_results():
    from app.routers.content import admin_list_results
    from app.schemas.jobs import ResultResponse

    res_obj = _make_result()
    with patch.object(
        ResultResponse, "model_validate", return_value=_mock_resp(res_obj.id)
    ):
        result = await admin_list_results(
            limit=20, offset=0, db=_db_list([res_obj]), admin=MagicMock()
        )
    assert result["pagination"]["total"] == 1


@pytest.mark.asyncio
async def test_admin_create_result_success():
    from app.routers.content import admin_create_result
    from app.schemas.jobs import ResultCreateRequest, ResultResponse

    job_id = uuid.uuid4()
    body = ResultCreateRequest(
        job_id=job_id, title="Final Result", slug="test-result", result_type="final"
    )
    db = AsyncMock()
    parent_res = MagicMock()
    parent_res.scalar.return_value = job_id
    slug_res = MagicMock()
    slug_res.scalar.return_value = None
    db.execute = AsyncMock(side_effect=[parent_res, slug_res])
    with patch.object(
        ResultResponse, "model_validate", return_value=_mock_resp(uuid.uuid4())
    ):
        await admin_create_result(body=body, admin=MagicMock(), db=db)
    db.add.assert_called_once()
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_admin_update_result_not_found():
    from app.routers.content import admin_update_result
    from app.schemas.jobs import ResultUpdateRequest
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await admin_update_result(
            result_id=uuid.uuid4(),
            body=ResultUpdateRequest(),
            admin=MagicMock(),
            db=_db_single(None),
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_admin_update_result_success():
    from app.routers.content import admin_update_result
    from app.schemas.jobs import ResultResponse, ResultUpdateRequest

    res_obj = _make_result()
    with patch.object(
        ResultResponse, "model_validate", return_value=_mock_resp(res_obj.id)
    ):
        await admin_update_result(
            result_id=res_obj.id,
            body=ResultUpdateRequest(title="Updated"),
            admin=MagicMock(),
            db=_db_single(res_obj),
        )


@pytest.mark.asyncio
async def test_admin_delete_result_not_found():
    from app.routers.content import admin_delete_result
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await admin_delete_result(
            result_id=uuid.uuid4(), admin=MagicMock(), db=_db_single(None)
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_admin_delete_result_success():
    from app.routers.content import admin_delete_result

    res_obj = _make_result()
    db = _db_single(res_obj)
    await admin_delete_result(result_id=res_obj.id, admin=MagicMock(), db=db)
    db.delete.assert_called_once_with(res_obj)
