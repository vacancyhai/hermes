"""Top-level content endpoints for admit cards, answer keys, and results.

Public endpoints:
  GET    /api/v1/admit-cards           — List all admit cards
  GET    /api/v1/admit-cards/{id}      — Get single admit card by ID
  GET    /api/v1/answer-keys           — List all answer keys
  GET    /api/v1/answer-keys/{id}      — Get single answer key by ID
  GET    /api/v1/results               — List all results
  GET    /api/v1/results/{id}          — Get single result by ID

Admin endpoints:
  POST   /api/v1/admin/admit-cards     — Create admit card
  PUT    /api/v1/admin/admit-cards/{id} — Update admit card
  DELETE /api/v1/admin/admit-cards/{id} — Delete admit card
  GET    /api/v1/admin/admit-cards     — List all admit cards (any status)

  POST   /api/v1/admin/answer-keys     — Create answer key
  PUT    /api/v1/admin/answer-keys/{id} — Update answer key
  DELETE /api/v1/admin/answer-keys/{id} — Delete answer key
  GET    /api/v1/admin/answer-keys     — List all answer keys (any status)

  POST   /api/v1/admin/results         — Create result
  PUT    /api/v1/admin/results/{id}     — Update result
  DELETE /api/v1/admin/results/{id}     — Delete result
  GET    /api/v1/admin/results         — List all results (any status)
"""

import json
import uuid
from datetime import date
from typing import Annotated, Any

from app.dependencies import get_db, get_redis, require_admin, require_operator
from app.models.admission import Admission
from app.models.admit_card import AdmitCard
from app.models.answer_key import AnswerKey
from app.models.job import Job
from app.models.result import Result
from app.schemas.admissions import AdmissionResponse
from app.schemas.jobs import (
    AdmitCardCreateRequest,
    AdmitCardResponse,
    AdmitCardUpdateRequest,
    AnswerKeyCreateRequest,
    AnswerKeyResponse,
    AnswerKeyUpdateRequest,
    JobResponse,
    ResultCreateRequest,
    ResultResponse,
    ResultUpdateRequest,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

_ERR_ADMIT_CARD_NOT_FOUND = "Admit card not found"
_ERR_ANSWER_KEY_NOT_FOUND = "Answer key not found"
_ERR_RESULT_NOT_FOUND = "Result not found"


def _paginated_response(
    items: list, schema, limit: int, offset: int, total: int
) -> dict:
    """Wrap a list of ORM objects into the standard paginated API envelope."""
    return {
        "data": [schema.model_validate(i).model_dump() for i in items],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


async def _enrich_with_parent(data: dict, obj, db: AsyncSession) -> dict:
    """Attach full job or admission data (with nested docs) to a document response."""
    if getattr(obj, "job", None):
        job = obj.job
        org_ref = getattr(job, "organization_ref", None)
        job_data = JobResponse.model_validate(job).model_dump()
        job_data["organization_logo_url"] = org_ref.logo_url if org_ref else None
        # Fetch nested docs for the parent job
        admit_cards = [
            AdmitCardResponse.model_validate(c).model_dump()
            for c in (
                await db.execute(
                    select(AdmitCard)
                    .where(AdmitCard.job_id == job.id)
                    .order_by(AdmitCard.published_at.desc())
                )
            )
            .scalars()
            .all()
        ]
        answer_keys = [
            AnswerKeyResponse.model_validate(k).model_dump()
            for k in (
                await db.execute(
                    select(AnswerKey)
                    .where(AnswerKey.job_id == job.id)
                    .order_by(AnswerKey.published_at.desc())
                )
            )
            .scalars()
            .all()
        ]
        results = [
            ResultResponse.model_validate(r).model_dump()
            for r in (
                await db.execute(
                    select(Result)
                    .where(Result.job_id == job.id)
                    .order_by(Result.published_at.desc())
                )
            )
            .scalars()
            .all()
        ]
        job_data["admit_cards"] = admit_cards
        job_data["answer_keys"] = answer_keys
        job_data["results"] = results
        data["job"] = job_data
    elif getattr(obj, "admission", None):
        admission = obj.admission
        adm_data = AdmissionResponse.model_validate(admission).model_dump()
        # Fetch nested docs for the parent admission
        admit_cards = [
            AdmitCardResponse.model_validate(c).model_dump()
            for c in (
                await db.execute(
                    select(AdmitCard)
                    .where(AdmitCard.admission_id == admission.id)
                    .order_by(AdmitCard.published_at.desc())
                )
            )
            .scalars()
            .all()
        ]
        answer_keys = [
            AnswerKeyResponse.model_validate(k).model_dump()
            for k in (
                await db.execute(
                    select(AnswerKey)
                    .where(AnswerKey.admission_id == admission.id)
                    .order_by(AnswerKey.published_at.desc())
                )
            )
            .scalars()
            .all()
        ]
        results = [
            ResultResponse.model_validate(r).model_dump()
            for r in (
                await db.execute(
                    select(Result)
                    .where(Result.admission_id == admission.id)
                    .order_by(Result.published_at.desc())
                )
            )
            .scalars()
            .all()
        ]
        adm_data["admit_cards"] = admit_cards
        adm_data["answer_keys"] = answer_keys
        adm_data["results"] = results
        data["admission"] = adm_data
    return data


async def _admin_list_docs(
    model,
    schema,
    db: AsyncSession,
    limit: int,
    offset: int,
    job_id: uuid.UUID | None,
    admission_id: uuid.UUID | None,
) -> dict:
    """Shared paginated list query for document admin endpoints."""
    query = select(model).order_by(
        model.published_at.desc().nulls_last(), model.created_at.desc()
    )
    count_query = select(func.count(model.id))
    if job_id:
        query = query.where(model.job_id == job_id)
        count_query = count_query.where(model.job_id == job_id)
    if admission_id:
        query = query.where(model.admission_id == admission_id)
        count_query = count_query.where(model.admission_id == admission_id)
    total = (await db.execute(count_query)).scalar()
    rows = (await db.execute(query.offset(offset).limit(limit))).scalars().all()
    return _paginated_response(rows, schema, limit, offset, total)


async def _admin_delete_doc(
    model, doc_id: uuid.UUID, not_found_msg: str, db: AsyncSession
) -> None:
    """Shared delete logic for document admin endpoints."""
    doc = (
        await db.execute(select(model).where(model.id == doc_id))
    ).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_msg)
    await db.delete(doc)


async def _validate_document_parent(
    job_id: uuid.UUID | None,
    admission_id: uuid.UUID | None,
    db: AsyncSession,
) -> None:
    """Raise 400 unless exactly one of job_id/admission_id is provided and the parent exists."""
    if bool(job_id) == bool(admission_id):
        detail = (
            "Cannot specify both job_id and admission_id"
            if job_id
            else "Must specify either job_id or admission_id"
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    if job_id:
        if not (await db.execute(select(Job.id).where(Job.id == job_id))).scalar():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
            )
    else:
        if not (
            await db.execute(select(Admission.id).where(Admission.id == admission_id))
        ).scalar():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Admission not found"
            )


# Public routers
admit_cards_router = APIRouter(prefix="/api/v1/admit-cards", tags=["admit-cards"])
answer_keys_router = APIRouter(prefix="/api/v1/answer-keys", tags=["answer-keys"])
results_router = APIRouter(prefix="/api/v1/results", tags=["results"])
exam_reminders_router = APIRouter(
    prefix="/api/v1/exam-reminders", tags=["exam-reminders"]
)

# Admin routers
admit_cards_admin_router = APIRouter(prefix="/api/v1/admin/admit-cards", tags=["admin"])
answer_keys_admin_router = APIRouter(prefix="/api/v1/admin/answer-keys", tags=["admin"])
results_admin_router = APIRouter(prefix="/api/v1/admin/results", tags=["admin"])


@admit_cards_router.get("")
async def list_admit_cards(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """List all admit cards from admit_cards table, ordered by published_at."""
    query = (
        select(AdmitCard)
        .options(
            joinedload(AdmitCard.job).joinedload(Job.organization_ref),
            joinedload(AdmitCard.admission),
        )
        .order_by(
            AdmitCard.published_at.desc().nulls_last(), AdmitCard.created_at.desc()
        )
    )
    count_query = select(func.count(AdmitCard.id))
    total = (await db.execute(count_query)).scalar()
    cards = (await db.execute(query.offset(offset).limit(limit))).scalars().all()

    def _card_item(c: AdmitCard) -> dict:
        d = AdmitCardResponse.model_validate(c).model_dump()
        if c.job:
            org_ref = getattr(c.job, "organization_ref", None)
            d["parent_type"] = "job"
            d["parent_title"] = c.job.job_title
            d["parent_organization"] = c.job.organization
            d["parent_slug"] = c.job.slug
            d["parent_logo_url"] = org_ref.logo_url if org_ref else None
        elif c.admission:
            d["parent_type"] = "admission"
            d["parent_title"] = c.admission.admission_name
            d["parent_organization"] = c.admission.conducting_body
            d["parent_slug"] = c.admission.slug
            d["parent_logo_url"] = None
        else:
            d["parent_type"] = None
            d["parent_title"] = None
            d["parent_organization"] = None
            d["parent_slug"] = None
            d["parent_logo_url"] = None
        return d

    return {
        "data": [_card_item(c) for c in cards],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@admit_cards_router.get("/{slug}")
async def get_admit_card(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get single admit card by slug with related job/admission."""
    query = (
        select(AdmitCard)
        .options(
            joinedload(AdmitCard.job).joinedload(Job.organization_ref),
            joinedload(AdmitCard.admission),
        )
        .where(AdmitCard.slug == slug)
    )

    result = await db.execute(query)
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_ADMIT_CARD_NOT_FOUND
        )

    return await _enrich_with_parent(
        AdmitCardResponse.model_validate(card).model_dump(), card, db
    )


@answer_keys_router.get("")
async def list_answer_keys(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """List all answer keys from job_answer_keys table, ordered by published_at."""
    query = (
        select(AnswerKey)
        .options(
            joinedload(AnswerKey.job).joinedload(Job.organization_ref),
            joinedload(AnswerKey.admission),
        )
        .order_by(
            AnswerKey.published_at.desc().nulls_last(), AnswerKey.created_at.desc()
        )
    )
    count_query = select(func.count(AnswerKey.id))
    total = (await db.execute(count_query)).scalar()
    keys = (await db.execute(query.offset(offset).limit(limit))).scalars().all()

    def _key_item(k: AnswerKey) -> dict:
        d = AnswerKeyResponse.model_validate(k).model_dump()
        if k.job:
            org_ref = getattr(k.job, "organization_ref", None)
            d["parent_type"] = "job"
            d["parent_title"] = k.job.job_title
            d["parent_organization"] = k.job.organization
            d["parent_slug"] = k.job.slug
            d["parent_logo_url"] = org_ref.logo_url if org_ref else None
        elif k.admission:
            d["parent_type"] = "admission"
            d["parent_title"] = k.admission.admission_name
            d["parent_organization"] = k.admission.conducting_body
            d["parent_slug"] = k.admission.slug
            d["parent_logo_url"] = None
        else:
            d["parent_type"] = None
            d["parent_title"] = None
            d["parent_organization"] = None
            d["parent_slug"] = None
            d["parent_logo_url"] = None
        return d

    return {
        "data": [_key_item(k) for k in keys],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@answer_keys_router.get("/{slug}")
async def get_answer_key(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get single answer key by slug with related job/admission."""
    query = (
        select(AnswerKey)
        .options(
            joinedload(AnswerKey.job).joinedload(Job.organization_ref),
            joinedload(AnswerKey.admission),
        )
        .where(AnswerKey.slug == slug)
    )

    result = await db.execute(query)
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_ANSWER_KEY_NOT_FOUND
        )

    return await _enrich_with_parent(
        AnswerKeyResponse.model_validate(key).model_dump(), key, db
    )


@results_router.get("")
async def list_results(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """List all results from results table, ordered by published_at."""
    query = (
        select(Result)
        .options(
            joinedload(Result.job).joinedload(Job.organization_ref),
            joinedload(Result.admission),
        )
        .order_by(Result.published_at.desc().nulls_last(), Result.created_at.desc())
    )
    count_query = select(func.count(Result.id))
    total = (await db.execute(count_query)).scalar()
    results_list = (await db.execute(query.offset(offset).limit(limit))).scalars().all()

    def _result_item(r: Result) -> dict:
        d = ResultResponse.model_validate(r).model_dump()
        if r.job:
            org_ref = getattr(r.job, "organization_ref", None)
            d["parent_type"] = "job"
            d["parent_title"] = r.job.job_title
            d["parent_organization"] = r.job.organization
            d["parent_slug"] = r.job.slug
            d["parent_logo_url"] = org_ref.logo_url if org_ref else None
        elif r.admission:
            d["parent_type"] = "admission"
            d["parent_title"] = r.admission.admission_name
            d["parent_organization"] = r.admission.conducting_body
            d["parent_slug"] = r.admission.slug
            d["parent_logo_url"] = None
        else:
            d["parent_type"] = None
            d["parent_title"] = None
            d["parent_organization"] = None
            d["parent_slug"] = None
            d["parent_logo_url"] = None
        return d

    return {
        "data": [_result_item(r) for r in results_list],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@results_router.get("/{slug}")
async def get_result(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get single result by slug with related job/admission."""
    query = (
        select(Result)
        .options(
            joinedload(Result.job).joinedload(Job.organization_ref),
            joinedload(Result.admission),
        )
        .where(Result.slug == slug)
    )

    result = await db.execute(query)
    result_obj = result.scalar_one_or_none()

    if not result_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_RESULT_NOT_FOUND
        )

    return await _enrich_with_parent(
        ResultResponse.model_validate(result_obj).model_dump(), result_obj, db
    )


# ADMIN — Admit Cards CRUD


@admit_cards_admin_router.get("")
async def admin_list_admit_cards(
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    job_id: Annotated[uuid.UUID | None, Query()] = None,
    admission_id: Annotated[uuid.UUID | None, Query()] = None,
):
    """Admin: List all admit cards (no filtering by parent status)."""
    return await _admin_list_docs(
        AdmitCard, AdmitCardResponse, db, limit, offset, job_id, admission_id
    )


@admit_cards_admin_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=AdmitCardResponse,
    responses={409: {"description": "Slug already in use"}},
)
async def admin_create_admit_card(
    body: AdmitCardCreateRequest,
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new admit card. Must specify either job_id or admission_id."""
    await _validate_document_parent(body.job_id, body.admission_id, db)
    if (
        await db.execute(select(AdmitCard.id).where(AdmitCard.slug == body.slug))
    ).scalar():
        raise HTTPException(
            status_code=409, detail=f"Slug '{body.slug}' is already in use"
        )
    doc = AdmitCard(
        slug=body.slug,
        job_id=body.job_id,
        admission_id=body.admission_id,
        title=body.title,
        links=body.links,
        exam_start=body.exam_start,
        exam_end=body.exam_end,
        published_at=body.published_at,
    )
    db.add(doc)
    await db.flush()
    return AdmitCardResponse.model_validate(doc)


@admit_cards_admin_router.put("/{card_id}", response_model=AdmitCardResponse)
async def admin_update_admit_card(
    card_id: uuid.UUID,
    body: AdmitCardUpdateRequest,
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update an admit card."""
    result = await db.execute(select(AdmitCard).where(AdmitCard.id == card_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_ADMIT_CARD_NOT_FOUND
        )

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)

    await db.flush()
    await db.refresh(doc)
    return AdmitCardResponse.model_validate(doc)


@admit_cards_admin_router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_admit_card(
    card_id: uuid.UUID,
    admin: Annotated[Any, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete an admit card."""
    await _admin_delete_doc(AdmitCard, card_id, _ERR_ADMIT_CARD_NOT_FOUND, db)


# ADMIN — Answer Keys CRUD


@answer_keys_admin_router.get("")
async def admin_list_answer_keys(
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    job_id: Annotated[uuid.UUID | None, Query()] = None,
    admission_id: Annotated[uuid.UUID | None, Query()] = None,
):
    """Admin: List all answer keys (no filtering by parent status)."""
    return await _admin_list_docs(
        AnswerKey, AnswerKeyResponse, db, limit, offset, job_id, admission_id
    )


@answer_keys_admin_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=AnswerKeyResponse,
    responses={409: {"description": "Slug already in use"}},
)
async def admin_create_answer_key(
    body: AnswerKeyCreateRequest,
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new answer key. Must specify either job_id or admission_id."""
    await _validate_document_parent(body.job_id, body.admission_id, db)
    if (
        await db.execute(select(AnswerKey.id).where(AnswerKey.slug == body.slug))
    ).scalar():
        raise HTTPException(
            status_code=409, detail=f"Slug '{body.slug}' is already in use"
        )
    doc = AnswerKey(
        slug=body.slug,
        job_id=body.job_id,
        admission_id=body.admission_id,
        title=body.title,
        links=body.links,
        start_date=body.start_date,
        end_date=body.end_date,
        published_at=body.published_at,
    )
    db.add(doc)
    await db.flush()
    return AnswerKeyResponse.model_validate(doc)


@answer_keys_admin_router.put("/{key_id}", response_model=AnswerKeyResponse)
async def admin_update_answer_key(
    key_id: uuid.UUID,
    body: AnswerKeyUpdateRequest,
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update an answer key."""
    result = await db.execute(select(AnswerKey).where(AnswerKey.id == key_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_ANSWER_KEY_NOT_FOUND
        )

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)

    await db.flush()
    await db.refresh(doc)
    return AnswerKeyResponse.model_validate(doc)


@answer_keys_admin_router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_answer_key(
    key_id: uuid.UUID,
    admin: Annotated[Any, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete an answer key."""
    await _admin_delete_doc(AnswerKey, key_id, _ERR_ANSWER_KEY_NOT_FOUND, db)


# ADMIN — Results CRUD


@results_admin_router.get("")
async def admin_list_results(
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    job_id: Annotated[uuid.UUID | None, Query()] = None,
    admission_id: Annotated[uuid.UUID | None, Query()] = None,
):
    """Admin: List all results (no filtering by parent status)."""
    return await _admin_list_docs(
        Result, ResultResponse, db, limit, offset, job_id, admission_id
    )


@results_admin_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ResultResponse,
    responses={409: {"description": "Slug already in use"}},
)
async def admin_create_result(
    body: ResultCreateRequest,
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new result. Must specify either job_id or admission_id."""
    await _validate_document_parent(body.job_id, body.admission_id, db)
    if (await db.execute(select(Result.id).where(Result.slug == body.slug))).scalar():
        raise HTTPException(
            status_code=409, detail=f"Slug '{body.slug}' is already in use"
        )
    doc = Result(
        slug=body.slug,
        job_id=body.job_id,
        admission_id=body.admission_id,
        title=body.title,
        links=body.links,
        start_date=body.start_date,
        end_date=body.end_date,
        published_at=body.published_at,
    )
    db.add(doc)
    await db.flush()
    return ResultResponse.model_validate(doc)


@results_admin_router.put("/{result_id}", response_model=ResultResponse)
async def admin_update_result(
    result_id: uuid.UUID,
    body: ResultUpdateRequest,
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a result."""
    result = await db.execute(select(Result).where(Result.id == result_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_RESULT_NOT_FOUND
        )

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)

    await db.flush()
    await db.refresh(doc)
    return ResultResponse.model_validate(doc)


@results_admin_router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_result(
    result_id: uuid.UUID,
    admin: Annotated[Any, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a result."""
    await _admin_delete_doc(Result, result_id, _ERR_RESULT_NOT_FOUND, db)


# ── Exam Reminders ─────────────────────────────────────────────────────────────────────────────


async def _query_job_exam_rows(db: AsyncSession, today: date):
    result = await db.execute(
        select(
            Job.id, Job.job_title.label("title"), Job.exam_start, Job.exam_end, Job.slug
        )
        .where(Job.exam_start >= today)
        .where(~select(AdmitCard.id).where(AdmitCard.job_id == Job.id).exists())
        .order_by(Job.exam_start)
    )
    return result.all()


async def _query_admission_exam_rows(db: AsyncSession, today: date):
    result = await db.execute(
        select(
            Admission.id,
            Admission.admission_name.label("title"),
            Admission.exam_start,
            Admission.exam_end,
            Admission.slug,
        )
        .where(Admission.exam_start >= today)
        .where(
            ~select(AdmitCard.id).where(AdmitCard.admission_id == Admission.id).exists()
        )
        .order_by(Admission.exam_start)
    )
    return result.all()


async def _query_admit_card_exam_rows(db: AsyncSession, today: date):
    result = await db.execute(
        select(
            AdmitCard.id,
            AdmitCard.title,
            AdmitCard.exam_start,
            AdmitCard.exam_end,
            AdmitCard.slug,
            AdmitCard.job_id,
            AdmitCard.admission_id,
            Job.slug.label("job_slug"),
            Admission.slug.label("admission_slug"),
        )
        .outerjoin(Job, Job.id == AdmitCard.job_id)
        .outerjoin(Admission, Admission.id == AdmitCard.admission_id)
        .where(AdmitCard.exam_start >= today)
        .order_by(AdmitCard.exam_start)
    )
    return result.all()


def _build_exam_items(type_: str, rows, today: date):
    items = []
    for row in rows:
        days = (row.exam_start - today).days if row.exam_start else None
        items.append(
            {
                "type": type_,
                "id": str(row.id),
                "title": row.title,
                "exam_start": str(row.exam_start) if row.exam_start else None,
                "exam_end": str(row.exam_end) if row.exam_end else None,
                "slug": row.slug,
                "days_remaining": days,
            }
        )
    return items


def _build_admit_card_exam_items(rows, today: date):
    items = []
    for row in rows:
        days = (row.exam_start - today).days if row.exam_start else None
        if row.job_id:
            parent_type = "job"
            parent_slug = row.job_slug or row.slug
            parent_id = str(row.job_id)
        elif row.admission_id:
            parent_type = "admission"
            parent_slug = row.admission_slug or row.slug
            parent_id = str(row.admission_id)
        else:
            parent_type, parent_slug, parent_id = "admit_card", row.slug, None
        items.append(
            {
                "type": "admit_card",
                "title": row.title,
                "exam_start": str(row.exam_start) if row.exam_start else None,
                "exam_end": str(row.exam_end) if row.exam_end else None,
                "slug": row.slug,
                "parent_type": parent_type,
                "parent_slug": parent_slug,
                "parent_id": parent_id,
                "days_remaining": days,
            }
        )
    return items


_EXAM_REMINDERS_CACHE_KEY = "exam_reminders:v1"
_EXAM_REMINDERS_TTL = 300  # 5 minutes


@exam_reminders_router.get("")
async def list_exam_reminders(
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Any, Depends(get_redis)],
):
    """Return upcoming exams sorted by exam_start.

    Logic:
    - Jobs/Admissions with no linked admit cards → use their own exam dates.
    - Admit cards → always shown individually (covers parent exam dates).
    """
    cached = await redis.get(_EXAM_REMINDERS_CACHE_KEY)
    if cached:
        return json.loads(cached)

    today = date.today()
    job_rows = await _query_job_exam_rows(db, today)
    admission_rows = await _query_admission_exam_rows(db, today)
    admit_card_rows = await _query_admit_card_exam_rows(db, today)

    all_items = (
        _build_exam_items("job", job_rows, today)
        + _build_exam_items("admission", admission_rows, today)
        + _build_admit_card_exam_items(admit_card_rows, today)
    )
    all_items.sort(key=lambda x: x["exam_start"] or "9999-99-99")

    result = {"data": all_items, "total": len(all_items)}
    await redis.setex(
        _EXAM_REMINDERS_CACHE_KEY, _EXAM_REMINDERS_TTL, json.dumps(result)
    )
    return result
