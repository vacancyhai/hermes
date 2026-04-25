"""Job vacancy endpoints (public).

GET    /api/v1/jobs                    — List (filterable, paginated, full-text search)
GET    /api/v1/jobs/eligibility/{slug} — Per-job eligibility check for logged-in user
GET    /api/v1/jobs/:id                — Detail by ID
"""

from typing import Annotated, Any

from app.dependencies import get_current_user, get_db
from app.models.admit_card import AdmitCard
from app.models.answer_key import AnswerKey
from app.models.job import Job
from app.models.organization import Organization
from app.models.result import Result
from app.models.user_profile import UserProfile
from app.schemas.jobs import (
    AdmitCardResponse,
    AnswerKeyResponse,
    JobListItem,
    JobResponse,
    ResultResponse,
)
from app.services.matching import check_job_eligibility
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("")
async def list_jobs(
    db: Annotated[AsyncSession, Depends(get_db)],
    q: Annotated[str | None, Query(description="Full-text search query")] = None,
    qualification_level: Annotated[str | None, Query()] = None,
    organization: Annotated[str | None, Query()] = None,
    department: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """List job vacancies with filters and full-text search. Excludes inactive jobs."""
    query = select(Job).where(Job.status != "inactive")
    count_query = select(func.count(Job.id)).where(Job.status != "inactive")

    # Full-text search
    if q:
        query = query.where(
            text("search_vector @@ plainto_tsquery('english', :q)")
        ).params(q=q)
        count_query = count_query.where(
            text("search_vector @@ plainto_tsquery('english', :q)")
        ).params(q=q)
        # Order by relevance when searching
        query = query.order_by(
            text("ts_rank(search_vector, plainto_tsquery('english', :q)) DESC").params(
                q=q
            )
        )

    # Filters
    if qualification_level:
        query = query.where(Job.qualification_level == qualification_level)
        count_query = count_query.where(Job.qualification_level == qualification_level)
    if organization:
        query = query.where(Job.organization.ilike(f"%{organization}%"))
        count_query = count_query.where(Job.organization.ilike(f"%{organization}%"))
    if department:
        query = query.where(Job.department.ilike(f"%{department}%"))
        count_query = count_query.where(Job.department.ilike(f"%{department}%"))
    # Default ordering (newest first) when not searching
    if not q:
        query = query.order_by(Job.created_at.desc())

    # Count total before pagination
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Paginate
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    jobs = result.scalars().all()

    # Fetch logo_urls for orgs referenced by these jobs in one query
    org_ids = [j.organization_id for j in jobs if j.organization_id]
    logo_map: dict = {}
    if org_ids:
        org_rows = await db.execute(
            select(Organization.id, Organization.logo_url).where(
                Organization.id.in_(org_ids)
            )
        )
        logo_map = {str(row.id): row.logo_url for row in org_rows}

    def _job_item(j: Job) -> dict:
        d = JobListItem.model_validate(j).model_dump()
        d["organization_logo_url"] = (
            logo_map.get(str(j.organization_id)) if j.organization_id else None
        )
        return d

    return {
        "data": [_job_item(j) for j in jobs],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@router.get("/eligibility/{slug}")
async def job_eligibility(
    slug: str,
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Return eligibility status for the current user against a specific job.

    Response: {"status": "eligible" | "partially_eligible" | "not_eligible", "reasons": [...]}
    """
    job_result = await db.execute(
        select(Job).where(Job.slug == slug, Job.status != "inactive")
    )
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    user, _ = current_user
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    profile = profile_result.scalar_one_or_none()

    from app.models.user_eligibility import UserJobEligibility

    cached = (
        await db.execute(
            select(UserJobEligibility).where(
                UserJobEligibility.user_id == user.id,
                UserJobEligibility.job_id == job.id,
            )
        )
    ).scalar_one_or_none()
    if cached:
        return {"status": cached.status, "reasons": cached.reasons}

    return check_job_eligibility(job, profile)


@router.get("/{slug}")
async def get_job(slug: str, db: Annotated[AsyncSession, Depends(get_db)]):
    """Get job detail by slug. Includes all related documents."""
    result = await db.execute(
        select(Job).where(Job.slug == slug, Job.status != "inactive")
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    job_id = job.id

    # Fetch related documents
    admit_cards_result = await db.execute(
        select(AdmitCard)
        .where(AdmitCard.job_id == job_id)
        .order_by(AdmitCard.published_at.desc())
    )
    admit_cards = [
        AdmitCardResponse.model_validate(card).model_dump()
        for card in admit_cards_result.scalars().all()
    ]

    answer_keys_result = await db.execute(
        select(AnswerKey)
        .where(AnswerKey.job_id == job_id)
        .order_by(AnswerKey.published_at.desc())
    )
    answer_keys = [
        AnswerKeyResponse.model_validate(key).model_dump()
        for key in answer_keys_result.scalars().all()
    ]

    results_result = await db.execute(
        select(Result)
        .where(Result.job_id == job_id)
        .order_by(Result.published_at.desc())
    )
    results = [
        ResultResponse.model_validate(res).model_dump()
        for res in results_result.scalars().all()
    ]

    # Build response with nested documents
    job_data = JobResponse.model_validate(job).model_dump()
    job_data["admit_cards"] = admit_cards
    job_data["answer_keys"] = answer_keys
    job_data["results"] = results

    return job_data
