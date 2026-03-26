"""Application tracking endpoints (requires user JWT).

GET    /api/v1/applications            — List own tracked applications
POST   /api/v1/applications            — Track / save a job
PUT    /api/v1/applications/:id        — Update application (status, notes, priority)
DELETE /api/v1/applications/:id        — Remove from tracker
GET    /api/v1/applications/stats      — Application stats (counts by status)
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

logger = logging.getLogger(__name__)
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.application import Application
from app.models.job import Job
from app.schemas.applications import (
    ApplicationCreateRequest,
    ApplicationResponse,
    ApplicationUpdateRequest,
)

router = APIRouter(prefix="/api/v1/applications", tags=["applications"])

VALID_STATUSES = {"applied", "admit_card_released", "exam_completed", "result_pending", "selected", "rejected", "waiting_list"}


@router.get("/stats")
async def application_stats(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Counts of applications grouped by status."""
    user, _ = current_user
    result = await db.execute(
        select(Application.status, func.count())
        .where(Application.user_id == user.id)
        .group_by(Application.status)
    )
    rows = result.all()
    counts = {row[0]: row[1] for row in rows}
    counts["total"] = sum(counts.values())
    return counts


@router.get("")
async def list_applications(
    status_filter: str | None = Query(None, alias="status"),
    is_priority: bool | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List own tracked applications with optional filters."""
    user, _ = current_user
    query = select(Application).where(Application.user_id == user.id)
    count_query = select(func.count(Application.id)).where(Application.user_id == user.id)

    if status_filter:
        query = query.where(Application.status == status_filter)
        count_query = count_query.where(Application.status == status_filter)
    if is_priority is not None:
        query = query.where(Application.is_priority == is_priority)
        count_query = count_query.where(Application.is_priority == is_priority)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Application.applied_on.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    apps = result.scalars().all()

    # Batch-fetch all related jobs in a single query (avoids N+1)
    job_ids = [app.job_id for app in apps]
    jobs_map: dict = {}
    if job_ids:
        jobs_result = await db.execute(select(Job).where(Job.id.in_(job_ids)))
        jobs_map = {j.id: j for j in jobs_result.scalars().all()}

    data = []
    for app in apps:
        job = jobs_map.get(app.job_id)
        item = ApplicationResponse.model_validate(app).model_dump()
        if job:
            item["job"] = {
                "job_title": job.job_title,
                "slug": job.slug,
                "organization": job.organization,
                "application_end": job.application_end.isoformat() if job.application_end else None,
            }
        data.append(item)

    return {
        "data": data,
        "pagination": {"limit": limit, "offset": offset, "total": total, "has_more": (offset + limit) < total},
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def track_job(
    body: ApplicationCreateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Track / save a job application."""
    user, _ = current_user

    # Verify job exists and is active
    job_result = await db.execute(select(Job).where(Job.id == body.job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Check duplicate (fast path for UX)
    existing = await db.execute(
        select(Application).where(
            Application.user_id == user.id,
            Application.job_id == body.job_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already tracking this job")

    app = Application(
        user_id=user.id,
        job_id=body.job_id,
        application_number=body.application_number,
        is_priority=body.is_priority,
        notes=body.notes,
        status=body.status or "applied",
    )
    db.add(app)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already tracking this job")

    # Atomic applications_count increment
    await db.execute(
        update(Job).where(Job.id == body.job_id)
        .values(applications_count=Job.applications_count + 1)
    )
    logger.info("application_tracked", extra={"user_id": str(user.id), "job_id": str(body.job_id)})

    item = ApplicationResponse.model_validate(app).model_dump()
    item["job"] = {
        "job_title": job.job_title,
        "slug": job.slug,
        "organization": job.organization,
        "application_end": job.application_end.isoformat() if job.application_end else None,
    }
    return item


@router.put("/{application_id}")
async def update_application(
    application_id: uuid.UUID,
    body: ApplicationUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an application (status, notes, priority, application_number)."""
    user, _ = current_user
    result = await db.execute(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == user.id,
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    update_data = body.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}",
        )

    for field, value in update_data.items():
        setattr(app, field, value)

    logger.info("application_updated", extra={"user_id": str(user.id), "application_id": str(application_id), "fields": list(update_data.keys())})
    return ApplicationResponse.model_validate(app).model_dump()


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_application(
    application_id: uuid.UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a job from the tracker."""
    user, _ = current_user
    result = await db.execute(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == user.id,
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    # Atomic applications_count decrement (floor at 0)
    await db.execute(
        update(Job).where(Job.id == app.job_id)
        .values(applications_count=func.greatest(Job.applications_count - 1, 0))
    )

    await db.delete(app)
    logger.info("application_removed", extra={"user_id": str(user.id), "application_id": str(application_id)})
