"""Public content endpoints for admit cards, answer keys, and results.

GET    /api/v1/admit-cards    — List all admit cards from job_admit_cards table
GET    /api/v1/answer-keys    — List all answer keys from job_answer_keys table
GET    /api/v1/results        — List all results from job_results table
"""

from fastapi import APIRouter, Depends, Query
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


@admit_cards_router.get("", response_model=list[AdmitCardResponse])
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

    return [AdmitCardResponse.model_validate(c) for c in cards]


@answer_keys_router.get("", response_model=list[AnswerKeyResponse])
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

    return [AnswerKeyResponse.model_validate(k) for k in keys]


@results_router.get("", response_model=list[ResultResponse])
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

    return [ResultResponse.model_validate(r) for r in results]
