"""Entrance exam endpoints (NEET, JEE, CLAT, CAT etc.).

Public (read-only):
  GET  /api/v1/entrance-exams              — list with stream/status/search filters
  GET  /api/v1/entrance-exams/:slug        — detail by slug
  GET  /api/v1/entrance-exams/:id/admit-cards   — per-phase admit cards
  GET  /api/v1/entrance-exams/:id/answer-keys   — per-phase answer keys
  GET  /api/v1/entrance-exams/:id/results       — per-phase results

Admin CRUD (operator+):
  POST   /api/v1/admin/entrance-exams
  PUT    /api/v1/admin/entrance-exams/:id
  DELETE /api/v1/admin/entrance-exams/:id

Note: Admin document CRUD has been moved to top-level endpoints:
  /api/v1/admin/admit-cards
  /api/v1/admin/answer-keys
  /api/v1/admin/results
"""

import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_admin_user, get_current_user, get_db, require_operator
from app.services.matching import get_recommended_entrance_exams
from app.models.entrance_exam import EntranceExam
from app.models.admit_card import AdmitCard
from app.models.answer_key import AnswerKey
from app.models.result import Result
from app.schemas.entrance_exams import (
    EntranceExamCreateRequest, EntranceExamUpdateRequest,
    EntranceExamListItem, EntranceExamResponse,
)
from app.schemas.jobs import (
    AdmitCardResponse,
    AnswerKeyResponse,
    ResultResponse,
)

public_router = APIRouter(prefix="/api/v1/entrance-exams", tags=["entrance-exams"])
admin_router = APIRouter(prefix="/api/v1/admin/entrance-exams", tags=["admin-entrance-exams"])


def _slugify(text_: str) -> str:
    slug = text_.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return re.sub(r"-+", "-", slug).strip("-")


async def _require_exam(exam_id: uuid.UUID, db: AsyncSession) -> EntranceExam:
    result = await db.execute(select(EntranceExam).where(EntranceExam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
    return exam


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC
# ══════════════════════════════════════════════════════════════════════════════


@public_router.get("")
async def list_exams(
    q: str | None = Query(None),
    stream: str | None = Query(None),
    exam_type: str | None = Query(None),
    is_featured: bool | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List entrance exams — all statuses."""
    query = select(EntranceExam)
    count_query = select(func.count(EntranceExam.id))

    if q:
        query = query.where(text("search_vector @@ plainto_tsquery('english', :q)")).params(q=q)
        count_query = count_query.where(text("search_vector @@ plainto_tsquery('english', :q)")).params(q=q)
        query = query.order_by(text("ts_rank(search_vector, plainto_tsquery('english', :q)) DESC").params(q=q))
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
        "pagination": {"limit": limit, "offset": offset, "total": total, "has_more": (offset + limit) < total},
    }


@public_router.get("/recommended")
async def recommended_exams(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Personalized entrance exam recommendations based on user profile."""
    user, _ = current_user
    exams, total = await get_recommended_entrance_exams(user.id, db, limit=limit, offset=offset)
    
    return {
        "data": [EntranceExamListItem.model_validate(e).model_dump() for e in exams],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@public_router.get("/by-id/{exam_id}")
async def get_exam_by_id(exam_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get entrance exam detail by ID (for partials, no view increment)."""
    result = await db.execute(select(EntranceExam).where(EntranceExam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
    return EntranceExamResponse.model_validate(exam).model_dump()


@public_router.get("/{slug}")
async def get_exam_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    """Get entrance exam detail by slug."""
    result = await db.execute(
        select(EntranceExam).where(EntranceExam.slug == slug)
    )
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
    # Increment view count
    await db.execute(
        update(EntranceExam).where(EntranceExam.id == exam.id).values(views=EntranceExam.views + 1)
    )
    await db.commit()
    return EntranceExamResponse.model_validate(exam).model_dump()


@public_router.get("/{exam_id}/admit-cards", response_model=list[AdmitCardResponse])
async def list_exam_admit_cards(exam_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Per-phase admit cards for an exam."""
    result = await db.execute(
        select(EntranceExam).where(EntranceExam.id == exam_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
    rows = await db.execute(
        select(AdmitCard)
        .where(AdmitCard.exam_id == exam_id)
        .order_by(AdmitCard.phase_number.nulls_last(), AdmitCard.published_at.desc())
    )
    return [AdmitCardResponse.model_validate(r) for r in rows.scalars().all()]


@public_router.get("/{exam_id}/answer-keys", response_model=list[AnswerKeyResponse])
async def list_exam_answer_keys(exam_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Per-phase answer keys for an exam."""
    result = await db.execute(
        select(EntranceExam).where(EntranceExam.id == exam_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
    rows = await db.execute(
        select(AnswerKey)
        .where(AnswerKey.exam_id == exam_id)
        .order_by(AnswerKey.phase_number.nulls_last(), AnswerKey.answer_key_type, AnswerKey.published_at.desc())
    )
    return [AnswerKeyResponse.model_validate(r) for r in rows.scalars().all()]


@public_router.get("/{exam_id}/results", response_model=list[ResultResponse])
async def list_exam_results(exam_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Per-phase results for an exam."""
    result = await db.execute(
        select(EntranceExam).where(EntranceExam.id == exam_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
    rows = await db.execute(
        select(Result)
        .where(Result.exam_id == exam_id)
        .order_by(Result.phase_number.nulls_last(), Result.published_at.desc())
    )
    return [ResultResponse.model_validate(r) for r in rows.scalars().all()]


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — exam CRUD
# ══════════════════════════════════════════════════════════════════════════════


@admin_router.get("")
async def admin_list_exams(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    stream: str | None = Query(None),
    exam_type: str | None = Query(None),
    status: str | None = Query(None),
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
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
    rows = (await db.execute(q.order_by(EntranceExam.created_at.desc()).offset(offset).limit(limit))).scalars().all()
    return {
        "data": [EntranceExamListItem.model_validate(r).model_dump() for r in rows],
        "pagination": {"limit": limit, "offset": offset, "total": total, "has_more": (offset + limit) < total},
    }


@admin_router.get("/{exam_id}")
async def admin_get_exam(
    exam_id: uuid.UUID,
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Get a single entrance exam by ID (any status)."""
    exam = await _require_exam(exam_id, db)
    return EntranceExamResponse.model_validate(exam).model_dump()


@admin_router.post("", status_code=status.HTTP_201_CREATED)
async def create_exam(
    body: EntranceExamCreateRequest,
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    base_slug = _slugify(body.exam_name)
    existing = {r[0] for r in (await db.execute(
        select(EntranceExam.slug).where(EntranceExam.slug.like(f"{base_slug}%"))
    )).all()}
    slug, counter = base_slug, 1
    while slug in existing:
        slug = f"{base_slug}-{counter}"
        counter += 1

    exam = EntranceExam(
        **body.model_dump(exclude_none=True),
        slug=slug,
        published_at=datetime.now(timezone.utc),
    )
    db.add(exam)
    await db.flush()
    return EntranceExamResponse.model_validate(exam).model_dump()


@admin_router.put("/{exam_id}")
async def update_exam(
    exam_id: uuid.UUID,
    body: EntranceExamUpdateRequest,
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    exam = await _require_exam(exam_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(exam, field, value)
    await db.flush()
    return EntranceExamResponse.model_validate(exam).model_dump()


@admin_router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exam(
    exam_id: uuid.UUID,
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    exam = await _require_exam(exam_id, db)
    await db.delete(exam)
