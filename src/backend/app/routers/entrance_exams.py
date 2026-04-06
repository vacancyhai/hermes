"""Entrance exam endpoints (NEET, JEE, CLAT, CAT etc.).

Public (read-only):
  GET  /api/v1/entrance-exams              — list with stream/status/search filters
  GET  /api/v1/entrance-exams/:id          — detail by ID

Admin CRUD (operator+):
  POST   /api/v1/admin/entrance-exams
  PUT    /api/v1/admin/entrance-exams/:id
  DELETE /api/v1/admin/entrance-exams/:id

Note: Admin document CRUD has been moved to top-level endpoints:
  /api/v1/admin/admit-cards
  /api/v1/admin/answer-keys
  /api/v1/admin/results
"""

import uuid
from datetime import datetime, timezone
from typing import Annotated, Any

from app.dependencies import get_current_user, get_db, require_operator
from app.models.admit_card import AdmitCard
from app.models.answer_key import AnswerKey
from app.models.entrance_exam import EntranceExam
from app.models.result import Result
from app.schemas.entrance_exams import (
    EntranceExamCreateRequest,
    EntranceExamListItem,
    EntranceExamResponse,
    EntranceExamUpdateRequest,
)
from app.schemas.jobs import AdmitCardResponse, AnswerKeyResponse, ResultResponse
from app.services.matching import get_recommended_entrance_exams
from app.utils import slugify as _slugify
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

public_router = APIRouter(prefix="/api/v1/entrance-exams", tags=["entrance-exams"])
admin_router = APIRouter(
    prefix="/api/v1/admin/entrance-exams", tags=["admin-entrance-exams"]
)


async def _require_exam(exam_id: uuid.UUID, db: AsyncSession) -> EntranceExam:
    result = await db.execute(select(EntranceExam).where(EntranceExam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found"
        )
    return exam


# PUBLIC


@public_router.get("")
async def list_exams(
    db: Annotated[AsyncSession, Depends(get_db)],
    q: Annotated[str | None, Query()] = None,
    stream: Annotated[str | None, Query()] = None,
    exam_type: Annotated[str | None, Query()] = None,
    is_featured: Annotated[bool | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """List entrance exams — all statuses."""
    query = select(EntranceExam)
    count_query = select(func.count(EntranceExam.id))

    if q:
        query = query.where(
            text("search_vector @@ plainto_tsquery('english', :q)")
        ).params(q=q)
        count_query = count_query.where(
            text("search_vector @@ plainto_tsquery('english', :q)")
        ).params(q=q)
        query = query.order_by(
            text("ts_rank(search_vector, plainto_tsquery('english', :q)) DESC").params(
                q=q
            )
        )
    else:
        query = query.order_by(EntranceExam.created_at.desc())

    if stream:
        query = query.where(EntranceExam.stream == stream)
        count_query = count_query.where(EntranceExam.stream == stream)
    if exam_type:
        query = query.where(EntranceExam.exam_type == exam_type)
        count_query = count_query.where(EntranceExam.exam_type == exam_type)
    if is_featured is not None:
        query = query.where(EntranceExam.is_featured == is_featured)
        count_query = count_query.where(EntranceExam.is_featured == is_featured)

    total = (await db.execute(count_query)).scalar()
    rows = (await db.execute(query.offset(offset).limit(limit))).scalars().all()

    # Increment views asynchronously (fire-and-forget style via bulk update)
    return {
        "data": [EntranceExamListItem.model_validate(r).model_dump() for r in rows],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@public_router.get("/recommended")
async def recommended_exams(
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Personalized entrance exam recommendations based on user profile."""
    user, _ = current_user
    exams, total = await get_recommended_entrance_exams(
        user.id, db, limit=limit, offset=offset
    )

    return {
        "data": [EntranceExamListItem.model_validate(e).model_dump() for e in exams],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@public_router.get("/{exam_id}")
async def get_exam(exam_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    """Get entrance exam detail by ID. Increments view count. Includes all related documents."""
    result = await db.execute(select(EntranceExam).where(EntranceExam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found"
        )
    # Increment view count (inline, committed with the response)
    await db.execute(
        update(EntranceExam)
        .where(EntranceExam.id == exam.id)
        .values(views=EntranceExam.views + 1)
    )
    await db.commit()

    # Fetch related documents
    admit_cards_result = await db.execute(
        select(AdmitCard)
        .where(AdmitCard.exam_id == exam_id)
        .order_by(AdmitCard.phase_number.nulls_last(), AdmitCard.published_at.desc())
    )
    admit_cards = [
        AdmitCardResponse.model_validate(card).model_dump()
        for card in admit_cards_result.scalars().all()
    ]

    answer_keys_result = await db.execute(
        select(AnswerKey)
        .where(AnswerKey.exam_id == exam_id)
        .order_by(
            AnswerKey.phase_number.nulls_last(),
            AnswerKey.answer_key_type,
            AnswerKey.published_at.desc(),
        )
    )
    answer_keys = [
        AnswerKeyResponse.model_validate(key).model_dump()
        for key in answer_keys_result.scalars().all()
    ]

    results_result = await db.execute(
        select(Result)
        .where(Result.exam_id == exam_id)
        .order_by(Result.phase_number.nulls_last(), Result.published_at.desc())
    )
    results = [
        ResultResponse.model_validate(res).model_dump()
        for res in results_result.scalars().all()
    ]

    # Build response with nested documents
    exam_data = EntranceExamResponse.model_validate(exam).model_dump()
    exam_data["admit_cards"] = admit_cards
    exam_data["answer_keys"] = answer_keys
    exam_data["results"] = results

    return exam_data


# ADMIN — exam CRUD


@admin_router.get("")
async def admin_list_exams(
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    stream: Annotated[str | None, Query()] = None,
    exam_type: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
):
    q = select(EntranceExam)
    cq = select(func.count(EntranceExam.id))
    if stream:
        q = q.where(EntranceExam.stream == stream)
        cq = cq.where(EntranceExam.stream == stream)
    if exam_type:
        q = q.where(EntranceExam.exam_type == exam_type)
        cq = cq.where(EntranceExam.exam_type == exam_type)
    if status:
        q = q.where(EntranceExam.status == status)
        cq = cq.where(EntranceExam.status == status)
    total = (await db.execute(cq)).scalar()
    rows = (
        (
            await db.execute(
                q.order_by(EntranceExam.created_at.desc()).offset(offset).limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return {
        "data": [EntranceExamListItem.model_validate(r).model_dump() for r in rows],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@admin_router.get("/{exam_id}")
async def admin_get_exam(
    exam_id: uuid.UUID,
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a single entrance exam by ID (any status)."""
    exam = await _require_exam(exam_id, db)
    return EntranceExamResponse.model_validate(exam).model_dump()


@admin_router.post("", status_code=status.HTTP_201_CREATED)
async def create_exam(
    body: EntranceExamCreateRequest,
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    base_slug = _slugify(body.exam_name)
    existing = {
        r[0]
        for r in (
            await db.execute(
                select(EntranceExam.slug).where(EntranceExam.slug.like(f"{base_slug}%"))
            )
        ).all()
    }
    slug, counter = base_slug, 1
    while slug in existing:
        slug = f"{base_slug}-{counter}"
        counter += 1

    exam = EntranceExam(
        **body.model_dump(exclude_none=True),
        slug=slug,
        published_at=datetime.now(timezone.utc) if body.status == "active" else None,
    )
    db.add(exam)
    await db.flush()
    return EntranceExamResponse.model_validate(exam).model_dump()


@admin_router.put("/{exam_id}")
async def update_exam(
    exam_id: uuid.UUID,
    body: EntranceExamUpdateRequest,
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    exam = await _require_exam(exam_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(exam, field, value)
    await db.flush()
    await db.refresh(exam)
    return EntranceExamResponse.model_validate(exam).model_dump()


@admin_router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exam(
    exam_id: uuid.UUID,
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    exam = await _require_exam(exam_id, db)
    await db.delete(exam)
