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

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.dependencies import get_admin_user, get_current_user, get_db
from app.models.admit_card import AdmitCard
from app.models.answer_key import AnswerKey
from app.models.job import Job
from app.models.entrance_exam import EntranceExam
from app.models.result import Result
from app.schemas.jobs import (
    AdmitCardCreate,
    AdmitCardResponse,
    AdmitCardUpdateRequest,
    AnswerKeyCreate,
    AnswerKeyResponse,
    AnswerKeyUpdateRequest,
    ResultCreate,
    ResultResponse,
    ResultCreateRequest,
    ResultUpdateRequest,
)
from app.services.matching import (
    get_recommended_admit_cards,
    get_recommended_answer_keys,
    get_recommended_results,
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
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all admit cards from job_admit_cards table, ordered by published_at."""
    query = select(AdmitCard).order_by(AdmitCard.published_at.desc().nulls_last(), AdmitCard.created_at.desc())
    count_query = select(func.count(AdmitCard.id))

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.offset(offset).limit(limit))
    cards = result.scalars().all()

    return {
        "data": [AdmitCardResponse.model_validate(c).model_dump() for c in cards],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@admit_cards_router.get("/recommended")
async def recommended_admit_cards(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Personalized admit card recommendations based on user profile."""
    user, _ = current_user
    cards, total = await get_recommended_admit_cards(user.id, db, limit=limit, offset=offset)
    
    return {
        "data": [AdmitCardResponse.model_validate(c).model_dump() for c in cards],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@admit_cards_router.get("/{card_id}")
async def get_admit_card(
    card_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get single admit card by ID with related job/exam."""
    query = select(AdmitCard).options(
        joinedload(AdmitCard.job),
        joinedload(AdmitCard.exam)
    ).where(AdmitCard.id == card_id)
    
    result = await db.execute(query)
    card = result.scalar_one_or_none()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admit card not found"
        )
    
    card_data = AdmitCardResponse.model_validate(card).model_dump()
    
    # Add job/exam context
    if card.job:
        card_data["job"] = {
            "id": str(card.job.id),
            "slug": card.job.slug,
            "job_title": card.job.job_title,
            "organization": card.job.organization
        }
    elif card.exam:
        card_data["exam"] = {
            "id": str(card.exam.id),
            "slug": card.exam.slug,
            "exam_name": card.exam.exam_name,
            "conducting_body": card.exam.conducting_body
        }
    
    return card_data


@answer_keys_router.get("")
async def list_answer_keys(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all answer keys from job_answer_keys table, ordered by published_at."""
    query = select(AnswerKey).order_by(AnswerKey.published_at.desc().nulls_last(), AnswerKey.created_at.desc())
    count_query = select(func.count(AnswerKey.id))

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.offset(offset).limit(limit))
    keys = result.scalars().all()

    return {
        "data": [AnswerKeyResponse.model_validate(k).model_dump() for k in keys],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@answer_keys_router.get("/recommended")
async def recommended_answer_keys(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Personalized answer key recommendations based on user profile."""
    user, _ = current_user
    keys, total = await get_recommended_answer_keys(user.id, db, limit=limit, offset=offset)
    
    return {
        "data": [AnswerKeyResponse.model_validate(k).model_dump() for k in keys],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@answer_keys_router.get("/{key_id}")
async def get_answer_key(
    key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get single answer key by ID with related job/exam."""
    query = select(AnswerKey).options(
        joinedload(AnswerKey.job),
        joinedload(AnswerKey.exam)
    ).where(AnswerKey.id == key_id)
    
    result = await db.execute(query)
    key = result.scalar_one_or_none()
    
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer key not found"
        )
    
    key_data = AnswerKeyResponse.model_validate(key).model_dump()
    
    # Add job/exam context
    if key.job:
        key_data["job"] = {
            "id": str(key.job.id),
            "slug": key.job.slug,
            "job_title": key.job.job_title,
            "organization": key.job.organization
        }
    elif key.exam:
        key_data["exam"] = {
            "id": str(key.exam.id),
            "slug": key.exam.slug,
            "exam_name": key.exam.exam_name,
            "conducting_body": key.exam.conducting_body
        }
    
    return key_data


@results_router.get("")
async def list_results(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all results from job_results table, ordered by published_at."""
    query = select(Result).order_by(Result.published_at.desc().nulls_last(), Result.created_at.desc())
    count_query = select(func.count(Result.id))

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.offset(offset).limit(limit))
    results_list = result.scalars().all()

    return {
        "data": [ResultResponse.model_validate(r).model_dump() for r in results_list],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@results_router.get("/recommended")
async def recommended_results(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Personalized result recommendations based on user profile."""
    user, _ = current_user
    results_list, total = await get_recommended_results(user.id, db, limit=limit, offset=offset)
    
    return {
        "data": [ResultResponse.model_validate(r).model_dump() for r in results_list],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@results_router.get("/{result_id}")
async def get_result(
    result_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get single result by ID with related job/exam."""
    query = select(Result).options(
        joinedload(Result.job),
        joinedload(Result.exam)
    ).where(Result.id == result_id)
    
    result = await db.execute(query)
    result_obj = result.scalar_one_or_none()
    
    if not result_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )
    
    result_data = ResultResponse.model_validate(result_obj).model_dump()
    
    # Add job/exam context
    if result_obj.job:
        result_data["job"] = {
            "id": str(result_obj.job.id),
            "slug": result_obj.job.slug,
            "job_title": result_obj.job.job_title,
            "organization": result_obj.job.organization
        }
    elif result_obj.exam:
        result_data["exam"] = {
            "id": str(result_obj.exam.id),
            "slug": result_obj.exam.slug,
            "exam_name": result_obj.exam.exam_name,
            "conducting_body": result_obj.exam.conducting_body
        }
    
    return result_data


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — Admit Cards CRUD
# ══════════════════════════════════════════════════════════════════════════════


@admit_cards_admin_router.get("")
async def admin_list_admit_cards(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_operator),
):
    """Admin: List all admit cards (no filtering by parent status)."""
    query = select(AdmitCard).order_by(AdmitCard.published_at.desc().nulls_last(), AdmitCard.created_at.desc())
    count_query = select(func.count(AdmitCard.id))

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.offset(offset).limit(limit))
    cards = result.scalars().all()

    return {
        "data": [AdmitCardResponse.model_validate(c).model_dump() for c in cards],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@admit_cards_admin_router.post("", status_code=status.HTTP_201_CREATED, response_model=AdmitCardResponse)
async def admin_create_admit_card(
    body: AdmitCardCreateRequest,
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Create a new admit card. Must specify either job_id or exam_id."""
    # Validate that exactly one parent is specified
    if body.job_id and body.exam_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot specify both job_id and exam_id"
        )
    if not body.job_id and not body.exam_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify either job_id or exam_id"
        )
    
    # Validate parent exists
    if body.job_id:
        result = await db.execute(select(Job).where(Job.id == body.job_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    else:
        result = await db.execute(select(EntranceExam).where(EntranceExam.id == body.exam_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrance exam not found")
    
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
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Update an admit card."""
    result = await db.execute(select(AdmitCard).where(AdmitCard.id == card_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admit card not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)

    await db.flush()
    return AdmitCardResponse.model_validate(doc)


@admit_cards_admin_router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_admit_card(
    card_id: uuid.UUID,
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Delete an admit card."""
    result = await db.execute(select(AdmitCard).where(AdmitCard.id == card_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admit card not found")
    await db.delete(doc)


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — Answer Keys CRUD
# ══════════════════════════════════════════════════════════════════════════════


@answer_keys_admin_router.get("")
async def admin_list_answer_keys(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_operator),
):
    """Admin: List all answer keys (no filtering by parent status)."""
    query = select(AnswerKey).order_by(AnswerKey.published_at.desc().nulls_last(), AnswerKey.created_at.desc())
    count_query = select(func.count(AnswerKey.id))

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.offset(offset).limit(limit))
    keys = result.scalars().all()

    return {
        "data": [AnswerKeyResponse.model_validate(k).model_dump() for k in keys],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@answer_keys_admin_router.post("", status_code=status.HTTP_201_CREATED, response_model=AnswerKeyResponse)
async def admin_create_answer_key(
    body: AnswerKeyCreateRequest,
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Create a new answer key. Must specify either job_id or exam_id."""
    # Validate that exactly one parent is specified
    if body.job_id and body.exam_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot specify both job_id and exam_id"
        )
    if not body.job_id and not body.exam_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify either job_id or exam_id"
        )
    
    # Validate parent exists
    if body.job_id:
        result = await db.execute(select(Job).where(Job.id == body.job_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    else:
        result = await db.execute(select(EntranceExam).where(EntranceExam.id == body.exam_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrance exam not found")
    
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
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Update an answer key."""
    result = await db.execute(select(AnswerKey).where(AnswerKey.id == key_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer key not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)

    await db.flush()
    return AnswerKeyResponse.model_validate(doc)


@answer_keys_admin_router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_answer_key(
    key_id: uuid.UUID,
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Delete an answer key."""
    result = await db.execute(select(AnswerKey).where(AnswerKey.id == key_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer key not found")
    await db.delete(doc)


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — Results CRUD
# ══════════════════════════════════════════════════════════════════════════════


@results_admin_router.get("")
async def admin_list_results(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_operator),
):
    """Admin: List all results (no filtering by parent status)."""
    query = select(Result).order_by(Result.published_at.desc().nulls_last(), Result.created_at.desc())
    count_query = select(func.count(Result.id))

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.offset(offset).limit(limit))
    results = result.scalars().all()

    return {
        "data": [ResultResponse.model_validate(r).model_dump() for r in results],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@results_admin_router.post("", status_code=status.HTTP_201_CREATED, response_model=ResultResponse)
async def admin_create_result(
    body: ResultCreateRequest,
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Create a new result. Must specify either job_id or exam_id."""
    # Validate that exactly one parent is specified
    if body.job_id and body.exam_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot specify both job_id and exam_id"
        )
    if not body.job_id and not body.exam_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify either job_id or exam_id"
        )
    
    # Validate parent exists
    if body.job_id:
        result = await db.execute(select(Job).where(Job.id == body.job_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    else:
        result = await db.execute(select(EntranceExam).where(EntranceExam.id == body.exam_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrance exam not found")
    
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
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Update a result."""
    result = await db.execute(select(Result).where(Result.id == result_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)

    await db.flush()
    return ResultResponse.model_validate(doc)


@results_admin_router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_result(
    result_id: uuid.UUID,
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Delete a result."""
    result = await db.execute(select(Result).where(Result.id == result_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found")
    await db.delete(doc)
