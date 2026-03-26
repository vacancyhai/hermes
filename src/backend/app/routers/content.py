"""Public content endpoints for admit cards, answer keys, and results.

GET    /api/v1/admit-cards    — List admit cards (active only by default)
GET    /api/v1/answer-keys    — List answer keys (active only by default)
GET    /api/v1/results        — List results (active only by default)
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.job_vacancy import JobVacancy
from app.schemas.jobs import JobListItem

admit_cards_router = APIRouter(prefix="/api/v1/admit-cards", tags=["admit-cards"])
answer_keys_router = APIRouter(prefix="/api/v1/answer-keys", tags=["answer-keys"])
results_router = APIRouter(prefix="/api/v1/results", tags=["results"])


@admit_cards_router.get("")
async def list_admit_cards(
    q: str | None = Query(None, description="Full-text search query"),
    organization: str | None = Query(None),
    department: str | None = Query(None),
    is_featured: bool | None = Query(None),
    is_urgent: bool | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List admit cards with filters and search. Returns all admit cards."""
    query = select(JobVacancy).where(
        JobVacancy.job_type == "admit_card"
    )
    count_query = select(func.count(JobVacancy.id)).where(
        JobVacancy.job_type == "admit_card"
    )

    # Full-text search
    if q:
        query = query.where(text("search_vector @@ plainto_tsquery('english', :q)")).params(q=q)
        count_query = count_query.where(text("search_vector @@ plainto_tsquery('english', :q)")).params(q=q)
        query = query.order_by(text("ts_rank(search_vector, plainto_tsquery('english', :q)) DESC").params(q=q))

    # Filters
    if organization:
        query = query.where(JobVacancy.organization.ilike(f"%{organization}%"))
        count_query = count_query.where(JobVacancy.organization.ilike(f"%{organization}%"))
    if department:
        query = query.where(JobVacancy.department.ilike(f"%{department}%"))
        count_query = count_query.where(JobVacancy.department.ilike(f"%{department}%"))
    if is_featured is not None:
        query = query.where(JobVacancy.is_featured == is_featured)
        count_query = count_query.where(JobVacancy.is_featured == is_featured)
    if is_urgent is not None:
        query = query.where(JobVacancy.is_urgent == is_urgent)
        count_query = count_query.where(JobVacancy.is_urgent == is_urgent)

    # Default ordering (newest first) when not searching
    if not q:
        query = query.order_by(JobVacancy.created_at.desc())

    # Count and paginate
    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.offset(offset).limit(limit))
    jobs = result.scalars().all()

    return {
        "data": [JobListItem.model_validate(j).model_dump() for j in jobs],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@answer_keys_router.get("")
async def list_answer_keys(
    q: str | None = Query(None, description="Full-text search query"),
    organization: str | None = Query(None),
    department: str | None = Query(None),
    is_featured: bool | None = Query(None),
    is_urgent: bool | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List answer keys with filters and search. Returns all answer keys."""
    query = select(JobVacancy).where(
        JobVacancy.job_type == "answer_key"
    )
    count_query = select(func.count(JobVacancy.id)).where(
        JobVacancy.job_type == "answer_key"
    )

    # Full-text search
    if q:
        query = query.where(text("search_vector @@ plainto_tsquery('english', :q)")).params(q=q)
        count_query = count_query.where(text("search_vector @@ plainto_tsquery('english', :q)")).params(q=q)
        query = query.order_by(text("ts_rank(search_vector, plainto_tsquery('english', :q)) DESC").params(q=q))

    # Filters
    if organization:
        query = query.where(JobVacancy.organization.ilike(f"%{organization}%"))
        count_query = count_query.where(JobVacancy.organization.ilike(f"%{organization}%"))
    if department:
        query = query.where(JobVacancy.department.ilike(f"%{department}%"))
        count_query = count_query.where(JobVacancy.department.ilike(f"%{department}%"))
    if is_featured is not None:
        query = query.where(JobVacancy.is_featured == is_featured)
        count_query = count_query.where(JobVacancy.is_featured == is_featured)
    if is_urgent is not None:
        query = query.where(JobVacancy.is_urgent == is_urgent)
        count_query = count_query.where(JobVacancy.is_urgent == is_urgent)

    # Default ordering (newest first) when not searching
    if not q:
        query = query.order_by(JobVacancy.created_at.desc())

    # Count and paginate
    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.offset(offset).limit(limit))
    jobs = result.scalars().all()

    return {
        "data": [JobListItem.model_validate(j).model_dump() for j in jobs],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@results_router.get("")
async def list_results(
    q: str | None = Query(None, description="Full-text search query"),
    organization: str | None = Query(None),
    department: str | None = Query(None),
    is_featured: bool | None = Query(None),
    is_urgent: bool | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List results with filters and search. Returns all results."""
    query = select(JobVacancy).where(
        JobVacancy.job_type == "result"
    )
    count_query = select(func.count(JobVacancy.id)).where(
        JobVacancy.job_type == "result"
    )

    # Full-text search
    if q:
        query = query.where(text("search_vector @@ plainto_tsquery('english', :q)")).params(q=q)
        count_query = count_query.where(text("search_vector @@ plainto_tsquery('english', :q)")).params(q=q)
        query = query.order_by(text("ts_rank(search_vector, plainto_tsquery('english', :q)) DESC").params(q=q))

    # Filters
    if organization:
        query = query.where(JobVacancy.organization.ilike(f"%{organization}%"))
        count_query = count_query.where(JobVacancy.organization.ilike(f"%{organization}%"))
    if department:
        query = query.where(JobVacancy.department.ilike(f"%{department}%"))
        count_query = count_query.where(JobVacancy.department.ilike(f"%{department}%"))
    if is_featured is not None:
        query = query.where(JobVacancy.is_featured == is_featured)
        count_query = count_query.where(JobVacancy.is_featured == is_featured)
    if is_urgent is not None:
        query = query.where(JobVacancy.is_urgent == is_urgent)
        count_query = count_query.where(JobVacancy.is_urgent == is_urgent)

    # Default ordering (newest first) when not searching
    if not q:
        query = query.order_by(JobVacancy.created_at.desc())

    # Count and paginate
    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.offset(offset).limit(limit))
    jobs = result.scalars().all()

    return {
        "data": [JobListItem.model_validate(j).model_dump() for j in jobs],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }
