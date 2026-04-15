"""Admission endpoints (NEET, JEE, CLAT, CAT etc.).

Public (read-only):
  GET  /api/v1/admissions              — list with stream/status/search filters
  GET  /api/v1/admissions/:id          — detail by ID

Admin CRUD (operator+):
  POST   /api/v1/admin/admissions
  PUT    /api/v1/admin/admissions/:id
  DELETE /api/v1/admin/admissions/:id

Note: Admin document CRUD has been moved to top-level endpoints:
  /api/v1/admin/admit-cards
  /api/v1/admin/answer-keys
  /api/v1/admin/results
"""

import uuid
from datetime import datetime, timezone
from typing import Annotated, Any

from app.dependencies import get_current_user, get_db, require_operator
from app.models.admission import Admission
from app.models.admit_card import AdmitCard
from app.models.answer_key import AnswerKey
from app.models.result import Result
from app.schemas.admissions import (
    AdmissionCreateRequest,
    AdmissionListItem,
    AdmissionResponse,
    AdmissionUpdateRequest,
)
from app.schemas.jobs import AdmitCardResponse, AnswerKeyResponse, ResultResponse
from app.services.matching import get_recommended_admissions
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

public_router = APIRouter(prefix="/api/v1/admissions", tags=["admissions"])
admin_router = APIRouter(prefix="/api/v1/admin/admissions", tags=["admin-admissions"])


async def _require_admission(admission_id: uuid.UUID, db: AsyncSession) -> Admission:
    result = await db.execute(select(Admission).where(Admission.id == admission_id))
    admission = result.scalar_one_or_none()
    if not admission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Admission not found"
        )
    return admission


# PUBLIC


@public_router.get("")
async def list_admissions(
    db: Annotated[AsyncSession, Depends(get_db)],
    q: Annotated[str | None, Query()] = None,
    stream: Annotated[str | None, Query()] = None,
    admission_type: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """List admissions — excludes inactive."""
    query = select(Admission).where(Admission.status != "inactive")
    count_query = select(func.count(Admission.id)).where(Admission.status != "inactive")

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
        query = query.order_by(Admission.created_at.desc())

    if stream:
        query = query.where(Admission.stream == stream)
        count_query = count_query.where(Admission.stream == stream)
    if admission_type:
        query = query.where(Admission.admission_type == admission_type)
        count_query = count_query.where(Admission.admission_type == admission_type)
    total = (await db.execute(count_query)).scalar()
    rows = (await db.execute(query.offset(offset).limit(limit))).scalars().all()

    return {
        "data": [AdmissionListItem.model_validate(r).model_dump() for r in rows],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@public_router.get("/recommended")
async def recommended_admissions(
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Personalized admission recommendations based on user profile."""
    user, _ = current_user
    admissions, total = await get_recommended_admissions(
        user.id, db, limit=limit, offset=offset
    )

    return {
        "data": [AdmissionListItem.model_validate(e).model_dump() for e in admissions],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@public_router.get("/{slug}")
async def get_admission(slug: str, db: Annotated[AsyncSession, Depends(get_db)]):
    """Get admission detail by slug. Includes all related documents."""
    result = await db.execute(
        select(Admission).where(Admission.slug == slug, Admission.status != "inactive")
    )
    admission = result.scalar_one_or_none()
    if not admission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Admission not found"
        )
    admission_id = admission.id
    admit_cards_result = await db.execute(
        select(AdmitCard)
        .where(AdmitCard.admission_id == admission_id)
        .order_by(AdmitCard.phase_number.nulls_last(), AdmitCard.published_at.desc())
    )
    admit_cards = [
        AdmitCardResponse.model_validate(card).model_dump()
        for card in admit_cards_result.scalars().all()
    ]

    answer_keys_result = await db.execute(
        select(AnswerKey)
        .where(AnswerKey.admission_id == admission_id)
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
        .where(Result.admission_id == admission_id)
        .order_by(Result.phase_number.nulls_last(), Result.published_at.desc())
    )
    results = [
        ResultResponse.model_validate(res).model_dump()
        for res in results_result.scalars().all()
    ]

    admission_data = AdmissionResponse.model_validate(admission).model_dump()
    admission_data["admit_cards"] = admit_cards
    admission_data["answer_keys"] = answer_keys
    admission_data["results"] = results

    return admission_data


# ADMIN — admission CRUD


@admin_router.get("")
async def admin_list_admissions(
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    stream: Annotated[str | None, Query()] = None,
    admission_type: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
):
    q = select(Admission)
    cq = select(func.count(Admission.id))
    if stream:
        q = q.where(Admission.stream == stream)
        cq = cq.where(Admission.stream == stream)
    if admission_type:
        q = q.where(Admission.admission_type == admission_type)
        cq = cq.where(Admission.admission_type == admission_type)
    if status:
        q = q.where(Admission.status == status)
        cq = cq.where(Admission.status == status)
    total = (await db.execute(cq)).scalar()
    rows = (
        (
            await db.execute(
                q.order_by(Admission.created_at.desc()).offset(offset).limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return {
        "data": [AdmissionListItem.model_validate(r).model_dump() for r in rows],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@admin_router.get("/{admission_id}")
async def admin_get_admission(
    admission_id: uuid.UUID,
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a single admission by ID (any status)."""
    admission = await _require_admission(admission_id, db)
    return AdmissionResponse.model_validate(admission).model_dump()


@admin_router.post("", status_code=status.HTTP_201_CREATED)
async def create_admission(
    body: AdmissionCreateRequest,
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if (
        await db.execute(select(Admission.id).where(Admission.slug == body.slug))
    ).scalar():
        raise HTTPException(
            status_code=409, detail=f"Slug '{body.slug}' is already in use"
        )
    slug = body.slug

    admission = Admission(
        slug=slug,
        admission_name=body.admission_name,
        conducting_body=body.conducting_body,
        counselling_body=body.counselling_body,
        admission_type=body.admission_type,
        stream=body.stream,
        eligibility=body.eligibility,
        admission_details=body.admission_details,
        selection_process=body.selection_process,
        seats_info=body.seats_info,
        application_start=body.application_start,
        application_end=body.application_end,
        admission_date=body.admission_date,
        result_date=body.result_date,
        counselling_start=body.counselling_start,
        fee_general=body.fee_general,
        fee_obc=body.fee_obc,
        fee_sc_st=body.fee_sc_st,
        fee_ews=body.fee_ews,
        fee_female=body.fee_female,
        description=body.description,
        short_description=body.short_description,
        source_url=body.source_url,
        status=body.status,
        published_at=datetime.now(timezone.utc) if body.status == "active" else None,
    )
    db.add(admission)
    await db.flush()
    return AdmissionResponse.model_validate(admission).model_dump()


@admin_router.put("/{admission_id}")
async def update_admission(
    admission_id: uuid.UUID,
    body: AdmissionUpdateRequest,
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    admission = await _require_admission(admission_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(admission, field, value)
    await db.flush()
    await db.refresh(admission)
    return AdmissionResponse.model_validate(admission).model_dump()


@admin_router.delete("/{admission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admission(
    admission_id: uuid.UUID,
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    admission = await _require_admission(admission_id, db)
    await db.delete(admission)
