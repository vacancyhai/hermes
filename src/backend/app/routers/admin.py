"""Admin endpoints (requires admin/operator JWT).

Job Management:
  GET    /api/v1/admin/jobs              — List all jobs (any status)
  POST   /api/v1/admin/jobs              — Create job
  POST   /api/v1/admin/jobs/upload-pdf   — Upload PDF → AI extraction → draft job
  PUT    /api/v1/admin/jobs/:id          — Update job
  PUT    /api/v1/admin/jobs/:id/approve  — Approve draft → active
  DELETE /api/v1/admin/jobs/:id          — Soft delete

User Management:
  GET    /api/v1/admin/users             — List users
  GET    /api/v1/admin/users/:id         — User detail
  PUT    /api/v1/admin/users/:id/status  — Suspend/activate

Admin Account Management (admin role only):
  POST   /api/v1/admin/admin-users       — Create new admin/operator account

Dashboard:
  GET    /api/v1/admin/stats             — Dashboard counts (jobs, users, applications, new users this week)
  GET    /api/v1/admin/logs              — Admin activity logs
"""

import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, status
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.rate_limit import limiter
from app.dependencies import get_current_admin, get_db, require_admin, require_operator
from app.models.admin_log import AdminLog
from app.models.admin_user import AdminUser
from app.models.application import UserJobApplication
from app.models.job_vacancy import JobVacancy
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.jobs import JobCreateRequest, JobListItem, JobResponse, JobUpdateRequest

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# Operators can only modify these fields on an existing job
OPERATOR_ALLOWED_FIELDS = frozenset({
    "status", "description", "short_description",
    "notification_date", "application_start", "application_end",
    "exam_start", "exam_end", "result_date",
})


class UserStatusRequest(BaseModel):
    status: str


class AdminCreateRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, description="Minimum 8 characters")
    full_name: str = Field(min_length=1, max_length=255)
    role: str = "operator"
    phone: str | None = None
    department: str | None = None


_admin_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
    """Dashboard stats: counts by job type, users, applications, new users this week."""
    from app.models.entrance_exam import EntranceExam
    
    # Job counts by type
    jobs_total = (await db.execute(select(func.count(JobVacancy.id)))).scalar()
    jobs_active = (await db.execute(select(func.count(JobVacancy.id)).where(JobVacancy.status == "active"))).scalar()
    jobs_draft = (await db.execute(select(func.count(JobVacancy.id)).where(JobVacancy.status == "draft"))).scalar()
    
    # Separate counts for each job type
    latest_job_count = (await db.execute(
        select(func.count(JobVacancy.id)).where(JobVacancy.job_type == "latest_job")
    )).scalar()
    admit_card_count = (await db.execute(
        select(func.count(JobVacancy.id)).where(JobVacancy.job_type == "admit_card")
    )).scalar()
    answer_key_count = (await db.execute(
        select(func.count(JobVacancy.id)).where(JobVacancy.job_type == "answer_key")
    )).scalar()
    result_count = (await db.execute(
        select(func.count(JobVacancy.id)).where(JobVacancy.job_type == "result")
    )).scalar()
    
    # Entrance exams count
    entrance_exams_count = (await db.execute(select(func.count(EntranceExam.id)))).scalar()
    
    users_total = (await db.execute(select(func.count(User.id)))).scalar()
    users_active = (await db.execute(select(func.count(User.id)).where(User.status == "active"))).scalar()

    # New users this week
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    users_new_this_week = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= week_ago)
    )).scalar()

    # Application counts
    apps_total = (await db.execute(select(func.count(UserJobApplication.id)))).scalar()

    return {
        "jobs": {
            "total": jobs_total, 
            "active": jobs_active, 
            "draft": jobs_draft,
            "by_type": {
                "latest_job": latest_job_count,
                "admit_card": admit_card_count,
                "answer_key": answer_key_count,
                "result": result_count,
            }
        },
        "entrance_exams": {"total": entrance_exams_count},
        "users": {"total": users_total, "active": users_active, "new_this_week": users_new_this_week},
        "applications": {"total": apps_total},
    }


@router.get("/analytics")
async def platform_analytics(
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Platform analytics: demographics, application trends, popular orgs, notification stats."""
    from app.models.notification import Notification

    # User demographics — category breakdown
    profiles = await db.execute(
        select(UserProfile.category, func.count(UserProfile.id))
        .where(UserProfile.category.isnot(None))
        .group_by(UserProfile.category)
    )
    category_breakdown = {row[0]: row[1] for row in profiles.all()}

    # User demographics — qualification breakdown
    quals = await db.execute(
        select(UserProfile.highest_qualification, func.count(UserProfile.id))
        .where(UserProfile.highest_qualification.isnot(None))
        .group_by(UserProfile.highest_qualification)
    )
    qualification_breakdown = {row[0]: row[1] for row in quals.all()}

    # Application trends — daily counts for last 30 days
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    daily_apps = await db.execute(
        select(
            func.date_trunc("day", UserJobApplication.applied_on).label("day"),
            func.count(UserJobApplication.id),
        )
        .where(UserJobApplication.applied_on >= thirty_days_ago)
        .group_by("day")
        .order_by("day")
    )
    application_trends = [
        {"date": row[0].isoformat() if row[0] else None, "count": row[1]}
        for row in daily_apps.all()
    ]

    # Popular organizations — top 10 by job count
    popular_orgs = await db.execute(
        select(JobVacancy.organization, func.count(JobVacancy.id).label("job_count"))
        .where(JobVacancy.status == "active")
        .group_by(JobVacancy.organization)
        .order_by(func.count(JobVacancy.id).desc())
        .limit(10)
    )
    top_organizations = [{"organization": row[0], "job_count": row[1]} for row in popular_orgs.all()]

    # Application status breakdown
    status_counts = await db.execute(
        select(UserJobApplication.status, func.count(UserJobApplication.id))
        .group_by(UserJobApplication.status)
    )
    application_statuses = {row[0]: row[1] for row in status_counts.all()}

    # Notification stats
    notif_total = (await db.execute(select(func.count(Notification.id)))).scalar()
    notif_unread = (await db.execute(
        select(func.count(Notification.id)).where(Notification.is_read.is_(False))
    )).scalar()

    return {
        "demographics": {
            "categories": category_breakdown,
            "qualifications": qualification_breakdown,
        },
        "application_trends": application_trends,
        "application_statuses": application_statuses,
        "top_organizations": top_organizations,
        "notifications": {"total": notif_total, "unread": notif_unread},
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


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: uuid.UUID,
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Get a single job (admin view, any status)."""
    result = await db.execute(select(JobVacancy).where(JobVacancy.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobResponse.model_validate(job).model_dump()


@router.post("/jobs", status_code=status.HTTP_201_CREATED)
async def create_job(
    body: JobCreateRequest,
    request: Request,
    current_admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Create a job vacancy."""
    admin = current_admin

    # Generate unique slug: fetch all collisions in one query, pick next free suffix
    base_slug = _slugify(body.job_title)
    existing_slugs_result = await db.execute(
        select(JobVacancy.slug).where(JobVacancy.slug.like(f"{base_slug}%"))
    )
    existing_slugs = {row[0] for row in existing_slugs_result.all()}
    slug = base_slug
    counter = 1
    while slug in existing_slugs:
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
        fee_general=body.fee_general,
        fee_obc=body.fee_obc,
        fee_sc_st=body.fee_sc_st,
        fee_ews=body.fee_ews,
        fee_female=body.fee_female,
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

    # If created as active, notify org followers
    if body.status == "active":
        from app.tasks.notifications import send_new_job_notifications
        send_new_job_notifications.delay(str(job.id))

    return JobResponse.model_validate(job).model_dump()


@router.post("/jobs/upload-pdf", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("5/minute")
async def upload_pdf(
    file: UploadFile,
    request: Request,
    current_admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF notification → AI extraction → create draft job."""
    admin = current_admin

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are accepted")

    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are accepted")

    content = await file.read()
    max_bytes = settings.PDF_MAX_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds {settings.PDF_MAX_SIZE_MB}MB limit",
        )

    upload_dir = Path(settings.PDF_UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = re.sub(r"[^\w.\-]", "_", file.filename or "upload.pdf")
    file_id = uuid.uuid4().hex[:12]
    dest = upload_dir / f"{file_id}_{safe_name}"
    dest.write_bytes(content)

    from app.tasks.jobs import extract_job_from_pdf
    task = extract_job_from_pdf.delay(str(dest), str(admin.id))

    await _log_action(db, admin, "upload_pdf", "job_vacancy", details=f"PDF: {safe_name}", request=request)

    return {"message": "PDF uploaded, extraction in progress", "task_id": task.id, "filename": safe_name}


@router.put("/jobs/{job_id}")
async def update_job(
    job_id: uuid.UUID,
    body: JobUpdateRequest,
    request: Request,
    current_admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Update a job vacancy. Operators can only modify limited fields."""
    admin = current_admin
    result = await db.execute(select(JobVacancy).where(JobVacancy.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    changes = {}
    update_data = body.model_dump(exclude_unset=True)

    if admin.role == "operator":
        restricted = set(update_data.keys()) - OPERATOR_ALLOWED_FIELDS
        if restricted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operators cannot modify: {', '.join(sorted(restricted))}",
            )

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

    # Notify users who marked this job as priority
    from app.tasks.notifications import notify_priority_subscribers
    notify_priority_subscribers.delay(str(job.id))

    # If status changed to active, also notify org followers
    if "status" in changes and body.status == "active":
        from app.tasks.notifications import send_new_job_notifications
        send_new_job_notifications.delay(str(job.id))

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

    # Trigger notification to org followers (async Celery task)
    from app.tasks.notifications import send_new_job_notifications
    send_new_job_notifications.delay(str(job.id))

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
    body: UserStatusRequest,
    request: Request,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Suspend or activate a user (admin only). Also disables/enables Firebase account."""
    new_status = body.status
    if new_status not in ("active", "suspended"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status must be 'active' or 'suspended'")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    old_status = user.status
    user.status = new_status

    # Update Firebase account status if user has firebase_uid
    if user.firebase_uid:
        from app.firebase import init_firebase
        if init_firebase():
            try:
                import firebase_admin
                from firebase_admin import auth as fb_auth
                
                if new_status == "suspended":
                    fb_auth.update_user(user.firebase_uid, disabled=True)
                    logger.info("firebase_user_disabled", extra={"firebase_uid": user.firebase_uid})
                elif new_status == "active":
                    fb_auth.update_user(user.firebase_uid, disabled=False)
                    logger.info("firebase_user_enabled", extra={"firebase_uid": user.firebase_uid})
            except firebase_admin.auth.UserNotFoundError:
                logger.warning("firebase_user_not_found", extra={"firebase_uid": user.firebase_uid})
            except Exception as exc:
                logger.error("firebase_update_failed", extra={"firebase_uid": user.firebase_uid, "error": str(exc)})

    await _log_action(db, admin, "update_user_status", "user", user_id,
                      changes={"status": {"old": old_status, "new": new_status}}, request=request)

    return {"message": f"User status changed to {new_status}"}


@router.delete("/users/{user_id}")
async def delete_user_permanently(
    user_id: uuid.UUID,
    request: Request,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete a user from both PostgreSQL and Firebase (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    firebase_uid = user.firebase_uid
    user_email = user.email

    # Delete from Firebase first (if exists)
    if firebase_uid:
        from app.firebase import init_firebase
        if init_firebase():
            try:
                import firebase_admin
                from firebase_admin import auth as fb_auth
                fb_auth.delete_user(firebase_uid)
                logger.info("firebase_user_deleted", extra={"firebase_uid": firebase_uid, "email": user_email})
            except firebase_admin.auth.UserNotFoundError:
                logger.warning("firebase_user_already_deleted", extra={"firebase_uid": firebase_uid})
            except Exception as exc:
                logger.error("firebase_delete_failed", extra={"firebase_uid": firebase_uid, "error": str(exc)})
                # Continue with PostgreSQL deletion even if Firebase fails

    # Delete from PostgreSQL
    await db.delete(user)
    
    await _log_action(db, admin, "delete_user_permanently", "user", user_id,
                      details=f"Deleted user {user_email} from both systems", request=request)

    return {"message": "User permanently deleted from both PostgreSQL and Firebase"}


# ─── Admin Account Management ───────────────────────────────────────────────


@router.post("/admin-users", status_code=status.HTTP_201_CREATED)
async def create_admin_user(
    body: AdminCreateRequest,
    request: Request,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new admin or operator account. Admin role only.

    This is the only way to provision new admin/operator accounts — there is
    no self-registration or out-of-band seeding needed after the first account
    is created directly in the DB.
    """
    if body.role not in ("admin", "operator"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'admin' or 'operator'",
        )

    existing = await db.execute(select(AdminUser).where(AdminUser.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An admin user with that email already exists",
        )

    new_admin = AdminUser(
        email=body.email,
        password_hash=_admin_pwd_context.hash(body.password),
        full_name=body.full_name,
        role=body.role,
        phone=body.phone,
        department=body.department,
    )
    db.add(new_admin)
    await db.flush()

    await _log_action(
        db, admin, "create_admin_user", "admin_user", new_admin.id,
        details=f"Created {body.role} account: {body.email}", request=request,
    )

    from app.schemas.auth import AdminUserResponse
    return AdminUserResponse.model_validate(new_admin).model_dump()


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
