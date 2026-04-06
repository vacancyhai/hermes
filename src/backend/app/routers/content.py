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

import uuid
from typing import Annotated, Any

from app.dependencies import get_current_user, get_db, require_operator
from app.models.admit_card import AdmitCard
from app.models.answer_key import AnswerKey
from app.models.entrance_exam import EntranceExam
from app.models.job import Job
from app.models.result import Result
from app.schemas.jobs import (
    AdmitCardCreateRequest,
    AdmitCardResponse,
    AdmitCardUpdateRequest,
    AnswerKeyCreateRequest,
    AnswerKeyResponse,
    AnswerKeyUpdateRequest,
    ResultCreateRequest,
    ResultResponse,
    ResultUpdateRequest,
)
from app.services.matching import (
    get_recommended_admit_cards,
    get_recommended_answer_keys,
    get_recommended_results,
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


def _enrich_with_parent(data: dict, obj) -> dict:
    """Attach a minimal job or exam context dict to a document response."""
    if getattr(obj, "job", None):
        data["job"] = {
            "id": str(obj.job.id),
            "slug": obj.job.slug,
            "job_title": obj.job.job_title,
            "organization": obj.job.organization,
        }
    elif getattr(obj, "exam", None):
        data["exam"] = {
            "id": str(obj.exam.id),
            "slug": obj.exam.slug,
            "exam_name": obj.exam.exam_name,
            "conducting_body": obj.exam.conducting_body,
        }
    return data


async def _validate_document_parent(
    job_id: uuid.UUID | None,
    exam_id: uuid.UUID | None,
    db: AsyncSession,
) -> None:
    """Raise 400 unless exactly one of job_id/exam_id is provided and the parent exists."""
    if bool(job_id) == bool(exam_id):
        detail = (
            "Cannot specify both job_id and exam_id"
            if job_id
            else "Must specify either job_id or exam_id"
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    if job_id:
        if not (await db.execute(select(Job.id).where(Job.id == job_id))).scalar():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
            )
    else:
        if not (
            await db.execute(select(EntranceExam.id).where(EntranceExam.id == exam_id))
        ).scalar():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Entrance exam not found"
            )


# Public routers
admit_cards_router = APIRouter(prefix="/api/v1/admit-cards", tags=["admit-cards"])
answer_keys_router = APIRouter(prefix="/api/v1/answer-keys", tags=["answer-keys"])
results_router = APIRouter(prefix="/api/v1/results", tags=["results"])

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
    query = select(AdmitCard).order_by(
        AdmitCard.published_at.desc().nulls_last(), AdmitCard.created_at.desc()
    )
    count_query = select(func.count(AdmitCard.id))

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.offset(offset).limit(limit))
    cards = result.scalars().all()
    return _paginated_response(cards, AdmitCardResponse, limit, offset, total)


@admit_cards_router.get("/recommended")
async def recommended_admit_cards(
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Personalized admit card recommendations based on user profile."""
    user, _ = current_user
    cards, total = await get_recommended_admit_cards(
        user.id, db, limit=limit, offset=offset
    )
    return _paginated_response(cards, AdmitCardResponse, limit, offset, total)


@admit_cards_router.get("/{card_id}")
async def get_admit_card(
    card_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get single admit card by ID with related job/exam."""
    query = (
        select(AdmitCard)
        .options(joinedload(AdmitCard.job), joinedload(AdmitCard.exam))
        .where(AdmitCard.id == card_id)
    )

    result = await db.execute(query)
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_ADMIT_CARD_NOT_FOUND
        )

    return _enrich_with_parent(
        AdmitCardResponse.model_validate(card).model_dump(), card
    )


@answer_keys_router.get("")
async def list_answer_keys(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """List all answer keys from job_answer_keys table, ordered by published_at."""
    query = select(AnswerKey).order_by(
        AnswerKey.published_at.desc().nulls_last(), AnswerKey.created_at.desc()
    )
    count_query = select(func.count(AnswerKey.id))

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.offset(offset).limit(limit))
    keys = result.scalars().all()
    return _paginated_response(keys, AnswerKeyResponse, limit, offset, total)


@answer_keys_router.get("/recommended")
async def recommended_answer_keys(
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Personalized answer key recommendations based on user profile."""
    user, _ = current_user
    keys, total = await get_recommended_answer_keys(
        user.id, db, limit=limit, offset=offset
    )
    return _paginated_response(keys, AnswerKeyResponse, limit, offset, total)


@answer_keys_router.get("/{key_id}")
async def get_answer_key(
    key_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get single answer key by ID with related job/exam."""
    query = (
        select(AnswerKey)
        .options(joinedload(AnswerKey.job), joinedload(AnswerKey.exam))
        .where(AnswerKey.id == key_id)
    )

    result = await db.execute(query)
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_ANSWER_KEY_NOT_FOUND
        )

    return _enrich_with_parent(AnswerKeyResponse.model_validate(key).model_dump(), key)


@results_router.get("")
async def list_results(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """List all results from results table, ordered by published_at."""
    query = select(Result).order_by(
        Result.published_at.desc().nulls_last(), Result.created_at.desc()
    )
    count_query = select(func.count(Result.id))

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.offset(offset).limit(limit))
    results_list = result.scalars().all()
    return _paginated_response(results_list, ResultResponse, limit, offset, total)


@results_router.get("/recommended")
async def recommended_results(
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Personalized result recommendations based on user profile."""
    user, _ = current_user
    results_list, total = await get_recommended_results(
        user.id, db, limit=limit, offset=offset
    )
    return _paginated_response(results_list, ResultResponse, limit, offset, total)


@results_router.get("/{result_id}")
async def get_result(
    result_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get single result by ID with related job/exam."""
    query = (
        select(Result)
        .options(joinedload(Result.job), joinedload(Result.exam))
        .where(Result.id == result_id)
    )

    result = await db.execute(query)
    result_obj = result.scalar_one_or_none()

    if not result_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_RESULT_NOT_FOUND
        )

    return _enrich_with_parent(
        ResultResponse.model_validate(result_obj).model_dump(), result_obj
    )


# ADMIN — Admit Cards CRUD


@admit_cards_admin_router.get("")
async def admin_list_admit_cards(
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Admin: List all admit cards (no filtering by parent status)."""
    query = select(AdmitCard).order_by(
        AdmitCard.published_at.desc().nulls_last(), AdmitCard.created_at.desc()
    )
    count_query = select(func.count(AdmitCard.id))

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.offset(offset).limit(limit))
    cards = result.scalars().all()
    return _paginated_response(cards, AdmitCardResponse, limit, offset, total)


@admit_cards_admin_router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=AdmitCardResponse
)
async def admin_create_admit_card(
    body: AdmitCardCreateRequest,
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new admit card. Must specify either job_id or exam_id."""
    await _validate_document_parent(body.job_id, body.exam_id, db)
    doc = AdmitCard(
        job_id=body.job_id,
        exam_id=body.exam_id,
        phase_number=body.phase_number,
        title=body.title,
        download_url=body.download_url,
        valid_from=body.valid_from,
        valid_until=body.valid_until,
        notes=body.notes,
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
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete an admit card."""
    result = await db.execute(select(AdmitCard).where(AdmitCard.id == card_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_ADMIT_CARD_NOT_FOUND
        )
    await db.delete(doc)


# ADMIN — Answer Keys CRUD


@answer_keys_admin_router.get("")
async def admin_list_answer_keys(
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Admin: List all answer keys (no filtering by parent status)."""
    query = select(AnswerKey).order_by(
        AnswerKey.published_at.desc().nulls_last(), AnswerKey.created_at.desc()
    )
    count_query = select(func.count(AnswerKey.id))

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.offset(offset).limit(limit))
    keys = result.scalars().all()
    return _paginated_response(keys, AnswerKeyResponse, limit, offset, total)


@answer_keys_admin_router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=AnswerKeyResponse
)
async def admin_create_answer_key(
    body: AnswerKeyCreateRequest,
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new answer key. Must specify either job_id or exam_id."""
    await _validate_document_parent(body.job_id, body.exam_id, db)
    doc = AnswerKey(
        job_id=body.job_id,
        exam_id=body.exam_id,
        phase_number=body.phase_number,
        title=body.title,
        answer_key_type=body.answer_key_type,
        files=body.files,
        objection_url=body.objection_url,
        objection_deadline=body.objection_deadline,
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
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete an answer key."""
    result = await db.execute(select(AnswerKey).where(AnswerKey.id == key_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_ANSWER_KEY_NOT_FOUND
        )
    await db.delete(doc)


# ADMIN — Results CRUD


@results_admin_router.get("")
async def admin_list_results(
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Admin: List all results (no filtering by parent status)."""
    query = select(Result).order_by(
        Result.published_at.desc().nulls_last(), Result.created_at.desc()
    )
    count_query = select(func.count(Result.id))

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.offset(offset).limit(limit))
    results = result.scalars().all()
    return _paginated_response(results, ResultResponse, limit, offset, total)


@results_admin_router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=ResultResponse
)
async def admin_create_result(
    body: ResultCreateRequest,
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new result. Must specify either job_id or exam_id."""
    await _validate_document_parent(body.job_id, body.exam_id, db)
    doc = Result(
        job_id=body.job_id,
        exam_id=body.exam_id,
        phase_number=body.phase_number,
        title=body.title,
        result_type=body.result_type,
        download_url=body.download_url,
        cutoff_marks=body.cutoff_marks,
        total_qualified=body.total_qualified,
        notes=body.notes,
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
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a result."""
    result = await db.execute(select(Result).where(Result.id == result_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_RESULT_NOT_FOUND
        )
    await db.delete(doc)
