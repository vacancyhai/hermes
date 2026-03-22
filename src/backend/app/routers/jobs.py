"""Job vacancy endpoints (public).

GET    /api/v1/jobs              — List (filterable, paginated, full-text search)
GET    /api/v1/jobs/recommended  — Personalized recommendations based on profile
GET    /api/v1/jobs/:slug        — Detail by slug
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.job_vacancy import JobVacancy
from app.schemas.jobs import JobListItem, JobResponse
from app.services.matching import get_recommended_jobs

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("")
async def list_jobs(
    q: str | None = Query(None, description="Full-text search query"),
    job_type: str | None = Query(None),
    qualification_level: str | None = Query(None),
    organization: str | None = Query(None),
    department: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    is_featured: bool | None = Query(None),
    is_urgent: bool | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List jobs with filters and full-text search. Returns only active jobs by default."""
    query = select(JobVacancy)
    count_query = select(func.count(JobVacancy.id))

    # Default to active jobs for public listing
    effective_status = status_filter or "active"
    query = query.where(JobVacancy.status == effective_status)
    count_query = count_query.where(JobVacancy.status == effective_status)

    # Full-text search
    if q:
        ts_query = func.plainto_tsquery("english", q)
        query = query.where(text("search_vector @@ plainto_tsquery('english', :q)")).params(q=q)
        count_query = count_query.where(text("search_vector @@ plainto_tsquery('english', :q)")).params(q=q)
        # Order by relevance when searching
        query = query.order_by(text("ts_rank(search_vector, plainto_tsquery('english', :q)) DESC").params(q=q))

    # Filters
    if job_type:
        query = query.where(JobVacancy.job_type == job_type)
        count_query = count_query.where(JobVacancy.job_type == job_type)
    if qualification_level:
        query = query.where(JobVacancy.qualification_level == qualification_level)
        count_query = count_query.where(JobVacancy.qualification_level == qualification_level)
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

    # Count total before pagination
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Paginate
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
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


@router.get("/recommended")
async def recommended_jobs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Personalized job recommendations based on user profile preferences."""
    user, _ = current_user
    jobs, total = await get_recommended_jobs(user.id, db, limit=limit, offset=offset)

    return {
        "data": [JobListItem.model_validate(j).model_dump() for j in jobs],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@router.get("/{slug}")
async def get_job(slug: str, db: AsyncSession = Depends(get_db)):
    """Get job detail by slug. Increments view count."""
    result = await db.execute(select(JobVacancy).where(JobVacancy.slug == slug))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Increment views
    job.views += 1

    return JobResponse.model_validate(job).model_dump()
