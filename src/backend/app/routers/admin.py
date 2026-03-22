"""Admin endpoints (requires admin/operator JWT).

Job Management:
  GET    /api/v1/admin/jobs              — List all jobs (any status)
  POST   /api/v1/admin/jobs              — Create job
  PUT    /api/v1/admin/jobs/:id          — Update job
  PUT    /api/v1/admin/jobs/:id/approve  — Approve draft → active
  DELETE /api/v1/admin/jobs/:id          — Soft delete

User Management:
  GET    /api/v1/admin/users             — List users
  GET    /api/v1/admin/users/:id         — User detail
  PUT    /api/v1/admin/users/:id/status  — Suspend/activate

Dashboard:
  GET    /api/v1/admin/stats             — Dashboard counts
  GET    /api/v1/admin/logs              — Admin activity logs
"""

import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_admin, get_db, require_admin, require_operator
from app.models.admin_log import AdminLog
from app.models.admin_user import AdminUser
from app.models.job_vacancy import JobVacancy
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.jobs import JobCreateRequest, JobListItem, JobResponse, JobUpdateRequest

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _slugify(text: str) -> str:
    """Generate URL-safe slug from text."""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


async def _log_action(db: AsyncSession, admin: AdminUser, action: str, resource_type: str | None = None,
                      resource_id: uuid.UUID | None = None, details: str | None = None,
                      changes: dict | None = None, request: Request | None = None):
    """Create an admin audit log entry."""
    log = AdminLog(
        admin_id=admin.id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        changes=changes or {},
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.add(log)


# ─── Dashboard ───────────────────────────────────────────────────────────────


@router.get("/stats")
async def dashboard_stats(
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Dashboard stats: counts of jobs, users, applications."""
    jobs_total = (await db.execute(select(func.count(JobVacancy.id)))).scalar()
    jobs_active = (await db.execute(select(func.count(JobVacancy.id)).where(JobVacancy.status == "active"))).scalar()
    jobs_draft = (await db.execute(select(func.count(JobVacancy.id)).where(JobVacancy.status == "draft"))).scalar()
    users_total = (await db.execute(select(func.count(User.id)))).scalar()
    users_active = (await db.execute(select(func.count(User.id)).where(User.status == "active"))).scalar()

    return {
        "jobs": {"total": jobs_total, "active": jobs_active, "draft": jobs_draft},
        "users": {"total": users_total, "active": users_active},
    }


# ─── Job Management ─────────────────────────────────────────────────────────


@router.get("/jobs")
async def list_all_jobs(
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """List all jobs (admin view, any status)."""
    query = select(JobVacancy)
    count_query = select(func.count(JobVacancy.id))

    if status_filter:
        query = query.where(JobVacancy.status == status_filter)
        count_query = count_query.where(JobVacancy.status == status_filter)

    query = query.order_by(JobVacancy.created_at.desc())

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.offset(offset).limit(limit))
    jobs = result.scalars().all()

    return {
        "data": [JobListItem.model_validate(j).model_dump() for j in jobs],
        "pagination": {"limit": limit, "offset": offset, "total": total, "has_more": (offset + limit) < total},
    }


@router.post("/jobs", status_code=status.HTTP_201_CREATED)
async def create_job(
    body: JobCreateRequest,
    request: Request,
    current_admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Create a job vacancy."""
    admin = current_admin

    # Generate unique slug
    base_slug = _slugify(body.job_title)
    slug = base_slug
    counter = 1
    while True:
        existing = await db.execute(select(JobVacancy.id).where(JobVacancy.slug == slug))
        if not existing.scalar_one_or_none():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    job = JobVacancy(
        job_title=body.job_title,
        slug=slug,
        organization=body.organization,
        department=body.department,
        job_type=body.job_type,
        employment_type=body.employment_type,
        qualification_level=body.qualification_level,
        total_vacancies=body.total_vacancies,
        vacancy_breakdown=body.vacancy_breakdown,
        description=body.description,
        short_description=body.short_description,
        eligibility=body.eligibility,
        application_details=body.application_details,
        documents=body.documents,
        source_url=body.source_url,
        notification_date=body.notification_date,
        application_start=body.application_start,
        application_end=body.application_end,
        exam_start=body.exam_start,
        exam_end=body.exam_end,
        result_date=body.result_date,
        exam_details=body.exam_details,
        salary_initial=body.salary_initial,
        salary_max=body.salary_max,
        salary=body.salary,
        selection_process=body.selection_process,
        status=body.status,
        is_featured=body.is_featured,
        is_urgent=body.is_urgent,
        created_by=admin.id,
        source="manual",
        published_at=datetime.now(timezone.utc) if body.status == "active" else None,
    )
    db.add(job)
    await db.flush()

    await _log_action(db, admin, "create_job", "job_vacancy", job.id,
                      details=f"Created job: {body.job_title}", request=request)

    return JobResponse.model_validate(job).model_dump()


@router.put("/jobs/{job_id}")
async def update_job(
    job_id: uuid.UUID,
    body: JobUpdateRequest,
    request: Request,
    current_admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Update a job vacancy."""
    admin = current_admin
    result = await db.execute(select(JobVacancy).where(JobVacancy.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    changes = {}
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        old_value = getattr(job, field)
        if old_value != value:
            changes[field] = {"old": str(old_value), "new": str(value)}
            setattr(job, field, value)

    if not changes:
        return JobResponse.model_validate(job).model_dump()

    # If status changed to active, set published_at
    if "status" in changes and body.status == "active" and not job.published_at:
        job.published_at = datetime.now(timezone.utc)

    await _log_action(db, admin, "update_job", "job_vacancy", job.id,
                      changes=changes, request=request)

    return JobResponse.model_validate(job).model_dump()


@router.put("/jobs/{job_id}/approve")
async def approve_job(
    job_id: uuid.UUID,
    request: Request,
    current_admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Approve a draft job → set status to active."""
    admin = current_admin
    result = await db.execute(select(JobVacancy).where(JobVacancy.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.status != "draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft jobs can be approved")

    job.status = "active"
    job.published_at = datetime.now(timezone.utc)

    await _log_action(db, admin, "approve_job", "job_vacancy", job.id,
                      details=f"Approved: {job.job_title}", request=request)

    return JobResponse.model_validate(job).model_dump()


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: uuid.UUID,
    request: Request,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a job vacancy (admin only, not operators)."""
    result = await db.execute(select(JobVacancy).where(JobVacancy.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    job.status = "cancelled"

    await _log_action(db, admin, "delete_job", "job_vacancy", job.id,
                      details=f"Soft-deleted: {job.job_title}", request=request)


# ─── User Management ────────────────────────────────────────────────────────


@router.get("/users")
async def list_users(
    status_filter: str | None = Query(None, alias="status"),
    q: str | None = Query(None, description="Search by name or email"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """List all users with optional search and status filter."""
    query = select(User)
    count_query = select(func.count(User.id))

    if status_filter:
        query = query.where(User.status == status_filter)
        count_query = count_query.where(User.status == status_filter)

    if q:
        search = f"%{q}%"
        query = query.where(User.full_name.ilike(search) | User.email.ilike(search))
        count_query = count_query.where(User.full_name.ilike(search) | User.email.ilike(search))

    query = query.order_by(User.created_at.desc())

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.offset(offset).limit(limit))
    users = result.scalars().all()

    from app.schemas.auth import UserResponse
    return {
        "data": [UserResponse.model_validate(u).model_dump() for u in users],
        "pagination": {"limit": limit, "offset": offset, "total": total, "has_more": (offset + limit) < total},
    }


@router.get("/users/{user_id}")
async def get_user(
    user_id: uuid.UUID,
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Get user details with profile."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    profile_result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = profile_result.scalar_one_or_none()

    from app.schemas.auth import UserResponse
    user_data = UserResponse.model_validate(user).model_dump()
    if profile:
        user_data["profile"] = {
            "date_of_birth": str(profile.date_of_birth) if profile.date_of_birth else None,
            "gender": profile.gender,
            "category": profile.category,
            "state": profile.state,
            "city": profile.city,
            "highest_qualification": profile.highest_qualification,
        }

    return user_data


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: uuid.UUID,
    request: Request,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Suspend or activate a user (admin only)."""
    body = await request.json()
    new_status = body.get("status")
    if new_status not in ("active", "suspended"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status must be 'active' or 'suspended'")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    old_status = user.status
    user.status = new_status

    await _log_action(db, admin, "update_user_status", "user", user_id,
                      changes={"status": {"old": old_status, "new": new_status}}, request=request)

    return {"message": f"User status changed to {new_status}"}


# ─── Logs ────────────────────────────────────────────────────────────────────


@router.get("/logs")
async def admin_logs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin activity logs."""
    count_query = select(func.count(AdminLog.id))
    total = (await db.execute(count_query)).scalar()

    query = (
        select(AdminLog)
        .order_by(AdminLog.timestamp.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "data": [
            {
                "id": str(log.id),
                "admin_id": str(log.admin_id),
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": str(log.resource_id) if log.resource_id else None,
                "details": log.details,
                "changes": log.changes,
                "ip_address": str(log.ip_address) if log.ip_address else None,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            }
            for log in logs
        ],
        "pagination": {"limit": limit, "offset": offset, "total": total, "has_more": (offset + limit) < total},
    }
