"""Public content endpoints for admit cards, answer keys, and results.

GET    /api/v1/admit-cards       — List all admit cards from admit_cards table
GET    /api/v1/admit-cards/{id}  — Get single admit card by ID
GET    /api/v1/answer-keys       — List all answer keys from answer_keys table
GET    /api/v1/answer-keys/{id}  — Get single answer key by ID
GET    /api/v1/results           — List all results from results table
GET    /api/v1/results/{id}      — Get single result by ID
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.admit_card import AdmitCard
from app.models.answer_key import AnswerKey
from app.models.result import Result
from app.schemas.jobs import AdmitCardResponse, AnswerKeyResponse, ResultResponse

admit_cards_router = APIRouter(prefix="/api/v1/admit-cards", tags=["admit-cards"])
answer_keys_router = APIRouter(prefix="/api/v1/answer-keys", tags=["answer-keys"])
results_router = APIRouter(prefix="/api/v1/results", tags=["results"])


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


@admit_cards_router.get("/{card_id}")
async def get_admit_card(
    card_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get single admit card by ID."""
    result = await db.execute(select(AdmitCard).where(AdmitCard.id == card_id))
    card = result.scalar_one_or_none()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admit card not found"
        )
    
    return AdmitCardResponse.model_validate(card).model_dump()


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


@answer_keys_router.get("/{key_id}")
async def get_answer_key(
    key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get single answer key by ID."""
    result = await db.execute(select(AnswerKey).where(AnswerKey.id == key_id))
    key = result.scalar_one_or_none()
    
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer key not found"
        )
    
    return AnswerKeyResponse.model_validate(key).model_dump()


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


@results_router.get("/{result_id}")
async def get_result(
    result_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get single result by ID."""
    result = await db.execute(select(Result).where(Result.id == result_id))
    result_obj = result.scalar_one_or_none()
    
    if not result_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )
    
    return ResultResponse.model_validate(result_obj).model_dump()
