"""Admin endpoints (requires admin/operator JWT).

Job Management:
  GET    /api/v1/admin/jobs              — List all jobs (any status)
  POST   /api/v1/admin/jobs              — Create job
  PUT    /api/v1/admin/jobs/:id          — Update job
  DELETE /api/v1/admin/jobs/:id          — Hard delete

User Management:
  GET    /api/v1/admin/users             — List users
  GET    /api/v1/admin/users/:id         — User detail
  PUT    /api/v1/admin/users/:id/status  — Suspend/activate

Admin Account Management (admin role only):
  POST   /api/v1/admin/admin-users       — Create new admin/operator account

Dashboard:
  GET    /api/v1/admin/stats             — Dashboard counts (jobs, users, new users this week)
  GET    /api/v1/admin/logs              — Admin activity logs
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from app.dependencies import get_db, require_admin, require_operator
from app.models.admin_log import AdminLog
from app.models.admin_user import AdminUser
from app.models.admission import Admission
from app.models.admit_card import AdmitCard
from app.models.answer_key import AnswerKey
from app.models.job import Job
from app.models.organization import Organization
from app.models.result import Result
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.auth import AdminUserResponse, AdminUserUpdateRequest, UserResponse
from app.schemas.jobs import (
    JobCreateRequest,
    JobListItem,
    JobResponse,
    JobUpdateRequest,
)
from app.utils import slugify
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# Operators can only modify these fields on an existing job
OPERATOR_ALLOWED_FIELDS = frozenset(
    {
        "status",
        "description",
        "short_description",
        "notification_date",
        "application_start",
        "application_end",
        "exam_start",
        "exam_end",
        "result_date",
    }
)


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


def _collect_changes(obj, update_data: dict) -> dict:
    """Diff update_data against obj fields; apply changes and return a changes dict."""
    changes = {}
    for field, value in update_data.items():
        old_value = getattr(obj, field)
        if old_value != value:
            changes[field] = {
                "old": (
                    old_value if isinstance(old_value, (dict, list)) else str(old_value)
                ),
                "new": value if isinstance(value, (dict, list)) else str(value),
            }
            setattr(obj, field, value)
    return changes


_ERR_JOB_NOT_FOUND = "Job not found"
_ERR_USER_NOT_FOUND = "User not found"
_ERR_ADMIN_NOT_FOUND = "Admin user not found"


async def _log_action(
    db: AsyncSession,
    admin: AdminUser,
    action: str,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    details: str | None = None,
    changes: dict | None = None,
    request: Request | None = None,
):
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
    await db.flush()


# ─── Dashboard ───────────────────────────────────────────────────────────────


@router.get("/stats")
async def dashboard_stats(
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Dashboard stats: separate counts for jobs, admit cards, answer keys, results, admissions."""
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    jobs_count = (await db.execute(select(func.count(Job.id)))).scalar()
    jobs_active = (
        await db.execute(select(func.count(Job.id)).where(Job.status == "active"))
    ).scalar()
    admit_cards_count = (await db.execute(select(func.count(AdmitCard.id)))).scalar()
    answer_keys_count = (await db.execute(select(func.count(AnswerKey.id)))).scalar()
    results_count = (await db.execute(select(func.count(Result.id)))).scalar()
    admissions_count = (await db.execute(select(func.count(Admission.id)))).scalar()
    admissions_active = (
        await db.execute(
            select(func.count(Admission.id)).where(Admission.status == "active")
        )
    ).scalar()
    users_total = (await db.execute(select(func.count(User.id)))).scalar()
    users_active = (
        await db.execute(select(func.count(User.id)).where(User.status == "active"))
    ).scalar()
    users_new_this_week = (
        await db.execute(select(func.count(User.id)).where(User.created_at >= week_ago))
    ).scalar()

    return {
        "jobs": {"total": jobs_count, "active": jobs_active},
        "admit_cards": {"total": admit_cards_count},
        "answer_keys": {"total": answer_keys_count},
        "results": {"total": results_count},
        "admissions": {
            "total": admissions_count,
            "active": admissions_active,
        },
        "users": {
            "total": users_total,
            "active": users_active,
            "new_this_week": users_new_this_week,
        },
    }


# ─── Job Management ─────────────────────────────────────────────────────────


@router.get("/jobs")
async def list_jobs(
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """List all jobs."""
    query = select(Job)
    count_query = select(func.count(Job.id))

    if status_filter:
        query = query.where(Job.status == status_filter)
        count_query = count_query.where(Job.status == status_filter)

    query = query.order_by(Job.created_at.desc())

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


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: uuid.UUID,
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a single job (admin view, any status)."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_JOB_NOT_FOUND
        )
    return JobResponse.model_validate(job).model_dump()


@router.post(
    "/jobs",
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "Slug already in use"}},
)
async def create_job(
    body: JobCreateRequest,
    request: Request,
    current_admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a job vacancy."""
    admin = current_admin

    # Validate slug uniqueness
    if (await db.execute(select(Job.id).where(Job.slug == body.slug))).scalar():
        raise HTTPException(
            status_code=409, detail=f"Slug '{body.slug}' is already in use"
        )
    slug = body.slug

    job = Job(
        job_title=body.job_title,
        slug=slug,
        organization=body.organization,
        organization_id=body.organization_id,
        department=body.department,
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
        fee=body.fee,
        status=body.status,
        created_by=admin.id,
        source="manual",
        published_at=datetime.now(timezone.utc) if body.status == "active" else None,
    )
    db.add(job)
    await db.flush()

    await _log_action(
        db,
        admin,
        "create_job",
        "job",
        job.id,
        details=f"Created job: {body.job_title}",
        request=request,
    )

    from app.tasks.eligibility import recompute_eligibility_for_job

    recompute_eligibility_for_job.delay(str(job.id))

    # If created as active, notify trackers
    if body.status == "active":
        from app.tasks.notifications import (
            notify_trackers_on_update,
            send_new_job_notifications,
        )

        notify_trackers_on_update.delay("job", str(job.id))
        send_new_job_notifications.delay(str(job.id))

    return JobResponse.model_validate(job).model_dump()


@router.put("/jobs/{job_id}")
async def update_job(
    job_id: uuid.UUID,
    body: JobUpdateRequest,
    request: Request,
    current_admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a job vacancy. Operators can only modify limited fields."""
    admin = current_admin
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_JOB_NOT_FOUND
        )

    update_data = body.model_dump(exclude_unset=True)

    if admin.role == "operator":
        restricted = set(update_data.keys()) - OPERATOR_ALLOWED_FIELDS
        if restricted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operators cannot modify: {', '.join(sorted(restricted))}",
            )

    changes = _collect_changes(job, update_data)
    if not changes:
        return JobResponse.model_validate(job).model_dump()

    if "status" in changes and body.status == "active":
        if not job.published_at:
            job.published_at = datetime.now(timezone.utc)
        from app.tasks.notifications import notify_trackers_on_update

        notify_trackers_on_update.delay("job", str(job.id))

    await _log_action(
        db, admin, "update_job", "job", job.id, changes=changes, request=request
    )

    from app.tasks.eligibility import recompute_eligibility_for_job

    recompute_eligibility_for_job.delay(str(job_id))

    await db.refresh(job)
    return JobResponse.model_validate(job).model_dump()


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: uuid.UUID,
    request: Request,
    admin: Annotated[Any, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Hard-delete a job vacancy (admin only, not operators)."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_JOB_NOT_FOUND
        )

    await _log_action(
        db,
        admin,
        "delete_job",
        "job",
        job.id,
        details=f"Deleted: {job.job_title}",
        request=request,
    )

    await db.delete(job)


# ─── User Management ────────────────────────────────────────────────────────


@router.get("/users")
async def list_users(
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    q: Annotated[str | None, Query(description="Search by name or email")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
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
        count_query = count_query.where(
            User.full_name.ilike(search) | User.email.ilike(search)
        )

    query = query.order_by(User.created_at.desc())

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.offset(offset).limit(limit))
    users = result.scalars().all()

    return {
        "data": [UserResponse.model_validate(u).model_dump() for u in users],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@router.get("/users/{user_id}")
async def get_user(
    user_id: uuid.UUID,
    admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get user details with profile."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_USER_NOT_FOUND
        )

    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()

    user_data = UserResponse.model_validate(user).model_dump()
    if profile:
        user_data["profile"] = {
            "date_of_birth": (
                str(profile.date_of_birth) if profile.date_of_birth else None
            ),
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
    admin: Annotated[Any, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Suspend or activate a user (admin only). Also disables/enables Firebase account."""
    new_status = body.status
    if new_status not in ("active", "suspended"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'active' or 'suspended'",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_USER_NOT_FOUND
        )

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
                    logger.info(
                        "firebase_user_disabled",
                        extra={"firebase_uid": user.firebase_uid},
                    )
                elif new_status == "active":
                    fb_auth.update_user(user.firebase_uid, disabled=False)
                    logger.info(
                        "firebase_user_enabled",
                        extra={"firebase_uid": user.firebase_uid},
                    )
            except firebase_admin.auth.UserNotFoundError:
                logger.warning(
                    "firebase_user_not_found", extra={"firebase_uid": user.firebase_uid}
                )
            except Exception as exc:
                logger.error(
                    "firebase_update_failed",
                    extra={"firebase_uid": user.firebase_uid, "error": str(exc)},
                )

    await _log_action(
        db,
        admin,
        "update_user_status",
        "user",
        user_id,
        changes={"status": {"old": old_status, "new": new_status}},
        request=request,
    )

    return {"message": f"User status changed to {new_status}"}


@router.delete("/users/{user_id}")
async def delete_user_permanently(
    user_id: uuid.UUID,
    request: Request,
    admin: Annotated[Any, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Permanently delete a user from both PostgreSQL and Firebase (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_USER_NOT_FOUND
        )

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
                logger.info(
                    "firebase_user_deleted",
                    extra={"firebase_uid": firebase_uid, "email": user_email},
                )
            except firebase_admin.auth.UserNotFoundError:
                logger.warning(
                    "firebase_user_already_deleted",
                    extra={"firebase_uid": firebase_uid},
                )
            except Exception as exc:
                logger.error(
                    "firebase_delete_failed",
                    extra={"firebase_uid": firebase_uid, "error": str(exc)},
                )
                # Continue with PostgreSQL deletion even if Firebase fails

    # Delete from PostgreSQL
    await db.delete(user)

    await _log_action(
        db,
        admin,
        "delete_user_permanently",
        "user",
        user_id,
        details=f"Deleted user {user_email} from both systems",
        request=request,
    )

    return {"message": "User permanently deleted from both PostgreSQL and Firebase"}


# ─── Admin Self ──────────────────────────────────────────────────────────────


@router.get("/me")
async def get_admin_me(
    admin: Annotated[Any, Depends(require_operator)],
):
    """Return the currently authenticated admin/operator's profile."""
    return AdminUserResponse.model_validate(admin).model_dump()


# ─── Admin Account Management ───────────────────────────────────────────────


@router.post("/admin-users", status_code=status.HTTP_201_CREATED)
async def create_admin_user(
    body: AdminCreateRequest,
    request: Request,
    admin: Annotated[Any, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
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
        db,
        admin,
        "create_admin_user",
        "admin_user",
        new_admin.id,
        details=f"Created {body.role} account: {body.email}",
        request=request,
    )

    return AdminUserResponse.model_validate(new_admin).model_dump()


@router.get("/admin-users")
async def list_admin_users(
    admin: Annotated[Any, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """List all admin and operator accounts. Admin role only."""
    total = (await db.execute(select(func.count(AdminUser.id)))).scalar()
    users = (
        (
            await db.execute(
                select(AdminUser)
                .order_by(AdminUser.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return {
        "data": [AdminUserResponse.model_validate(u).model_dump() for u in users],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


@router.get("/admin-users/{admin_user_id}")
async def get_admin_user(
    admin_user_id: uuid.UUID,
    admin: Annotated[Any, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a single admin/operator account by ID. Admin role only."""
    target = (
        await db.execute(select(AdminUser).where(AdminUser.id == admin_user_id))
    ).scalar_one_or_none()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_ADMIN_NOT_FOUND
        )
    return AdminUserResponse.model_validate(target).model_dump()


@router.put("/admin-users/{admin_user_id}")
async def update_admin_user(
    admin_user_id: uuid.UUID,
    body: AdminUserUpdateRequest,
    request: Request,
    admin: Annotated[Any, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update an admin/operator account (name, phone, department, role, status). Admin role only."""
    target = (
        await db.execute(select(AdminUser).where(AdminUser.id == admin_user_id))
    ).scalar_one_or_none()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_ADMIN_NOT_FOUND
        )
    update_data = body.model_dump(exclude_unset=True)
    if "role" in update_data and update_data["role"] not in ("admin", "operator"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'admin' or 'operator'",
        )
    if "status" in update_data and update_data["status"] not in ("active", "suspended"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'active' or 'suspended'",
        )
    for field, value in update_data.items():
        setattr(target, field, value)
    await _log_action(
        db,
        admin,
        "update_admin_user",
        "admin_user",
        target.id,
        details=f"Updated fields: {', '.join(update_data.keys())}",
        request=request,
    )
    await db.flush()
    await db.refresh(target)
    return AdminUserResponse.model_validate(target).model_dump()


@router.delete("/admin-users/{admin_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin_user(
    admin_user_id: uuid.UUID,
    request: Request,
    admin: Annotated[Any, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete an admin/operator account. Admin role only. Cannot delete your own account."""
    if admin.id == admin_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own admin account",
        )
    target = (
        await db.execute(select(AdminUser).where(AdminUser.id == admin_user_id))
    ).scalar_one_or_none()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_ADMIN_NOT_FOUND
        )
    await _log_action(
        db,
        admin,
        "delete_admin_user",
        "admin_user",
        target.id,
        details=f"Deleted admin account: {target.email}",
        request=request,
    )
    await db.delete(target)


# ─── Logs ────────────────────────────────────────────────────────────────────


@router.get("/logs")
async def admin_logs(
    admin: Annotated[Any, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    admin_id: Annotated[uuid.UUID | None, Query()] = None,
    action: Annotated[str | None, Query(max_length=100)] = None,
    resource_type: Annotated[str | None, Query(max_length=100)] = None,
    date_from: Annotated[datetime | None, Query()] = None,
    date_to: Annotated[datetime | None, Query()] = None,
):
    """Admin activity logs with optional filters: admin_id, action, resource_type, date_from, date_to."""
    filters = []
    if admin_id:
        filters.append(AdminLog.admin_id == admin_id)
    if action:
        filters.append(AdminLog.action == action)
    if resource_type:
        filters.append(AdminLog.resource_type == resource_type)
    if date_from:
        filters.append(AdminLog.timestamp >= date_from)
    if date_to:
        filters.append(AdminLog.timestamp <= date_to)

    count_query = select(func.count(AdminLog.id)).where(*filters)
    total = (await db.execute(count_query)).scalar()

    query = (
        select(AdminLog)
        .where(*filters)
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
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": (offset + limit) < total,
        },
    }


# ─── Organizations ────────────────────────────────────────────────────────────


@router.get("/organizations")
async def admin_list_organizations(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[Any, Depends(require_operator)],
    limit: Annotated[int, Query(ge=1, le=200)] = 200,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: Annotated[str | None, Query(max_length=255)] = None,
):
    """List all organizations."""
    q = select(Organization).order_by(Organization.name)
    cq = select(func.count(Organization.id))
    if search:
        q = q.where(Organization.name.ilike(f"%{search}%"))
        cq = cq.where(Organization.name.ilike(f"%{search}%"))
    total = (await db.execute(cq)).scalar()
    orgs = (await db.execute(q.offset(offset).limit(limit))).scalars().all()
    return {
        "data": [
            {
                "id": str(o.id),
                "name": o.name,
                "slug": o.slug,
                "org_type": o.org_type,
                "short_name": o.short_name,
                "logo_url": o.logo_url,
                "website_url": o.website_url,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orgs
        ],
        "total": total,
    }


_ORG_NOT_FOUND = "Organization not found"
_ORG_TYPE_VALUES = ("jobs", "admissions", "both")
_ORG_TYPE_ERR = "org_type must be 'jobs', 'admissions', or 'both'"


def _apply_org_fields(org, body: dict) -> None:
    """Apply simple scalar fields from body onto org in-place."""
    for field in ("name", "short_name", "logo_url", "website_url", "org_type"):
        if field not in body:
            continue
        val = (body[field] or "").strip() or None
        if field in ("name", "org_type") and not val:
            raise HTTPException(status_code=422, detail=f"{field} cannot be empty")
        if field == "org_type" and val not in _ORG_TYPE_VALUES:
            raise HTTPException(status_code=422, detail=_ORG_TYPE_ERR)
        setattr(org, field, val)


@router.post(
    "/organizations",
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"description": "Name or slug conflict"},
        422: {"description": "Validation error"},
    },
)
async def admin_create_organization(
    body: dict,
    request: Request,
    current_admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new organization."""
    name = (body.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="name is required")
    existing = (
        await db.execute(select(Organization).where(Organization.name == name))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=409, detail=f"Organization '{name}' already exists"
        )
    slug = (body.get("slug") or slugify(name)).strip()
    slug_exists = (
        await db.execute(select(Organization).where(Organization.slug == slug))
    ).scalar_one_or_none()
    if slug_exists:
        raise HTTPException(status_code=409, detail=f"Slug '{slug}' already in use")
    org_type = (body.get("org_type") or "both").strip()
    if org_type not in _ORG_TYPE_VALUES:
        raise HTTPException(status_code=422, detail=_ORG_TYPE_ERR)
    org = Organization(
        name=name,
        slug=slug,
        org_type=org_type,
        short_name=(body.get("short_name") or "").strip() or None,
        logo_url=(body.get("logo_url") or "").strip() or None,
        website_url=(body.get("website_url") or "").strip() or None,
    )
    db.add(org)
    await db.flush()
    await _log_action(
        db,
        current_admin,
        "create_organization",
        "organization",
        org.id,
        details=f"Created organization: {name}",
        request=request,
    )
    return {
        "id": str(org.id),
        "name": org.name,
        "slug": org.slug,
        "org_type": org.org_type,
        "short_name": org.short_name,
        "logo_url": org.logo_url,
        "website_url": org.website_url,
    }


@router.get("/organizations/{org_id}", responses={404: {"description": _ORG_NOT_FOUND}})
async def admin_get_organization(
    org_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[Any, Depends(require_operator)],
):
    """Get a single organization by ID."""
    org = (
        await db.execute(select(Organization).where(Organization.id == org_id))
    ).scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail=_ORG_NOT_FOUND)
    return {
        "id": str(org.id),
        "name": org.name,
        "slug": org.slug,
        "org_type": org.org_type,
        "short_name": org.short_name,
        "logo_url": org.logo_url,
        "website_url": org.website_url,
        "created_at": org.created_at.isoformat() if org.created_at else None,
    }


@router.put(
    "/organizations/{org_id}",
    responses={
        404: {"description": _ORG_NOT_FOUND},
        409: {"description": "Slug conflict"},
        422: {"description": "Validation error"},
    },
)
async def admin_update_organization(
    org_id: uuid.UUID,
    body: dict,
    request: Request,
    current_admin: Annotated[Any, Depends(require_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update an organization."""
    org = (
        await db.execute(select(Organization).where(Organization.id == org_id))
    ).scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail=_ORG_NOT_FOUND)
    _apply_org_fields(org, body)
    if "slug" in body:
        new_slug = (body["slug"] or "").strip() or slugify(org.name)
        if new_slug != org.slug:
            clash = (
                await db.execute(
                    select(Organization).where(
                        Organization.slug == new_slug,
                        Organization.id != org_id,
                    )
                )
            ).scalar_one_or_none()
            if clash:
                raise HTTPException(
                    status_code=409, detail=f"Slug '{new_slug}' already in use"
                )
            org.slug = new_slug
    await _log_action(
        db,
        current_admin,
        "update_organization",
        "organization",
        org.id,
        details=f"Updated organization: {org.name}",
        request=request,
    )
    return {
        "id": str(org.id),
        "name": org.name,
        "slug": org.slug,
        "org_type": org.org_type,
        "short_name": org.short_name,
        "logo_url": org.logo_url,
        "website_url": org.website_url,
    }


@router.delete(
    "/organizations/{org_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"description": _ORG_NOT_FOUND}},
)
async def admin_delete_organization(
    org_id: uuid.UUID,
    request: Request,
    current_admin: Annotated[Any, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete an organization (admin only). Jobs linked will have organization_id set to NULL."""
    org = (
        await db.execute(select(Organization).where(Organization.id == org_id))
    ).scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail=_ORG_NOT_FOUND)
    await _log_action(
        db,
        current_admin,
        "delete_organization",
        "organization",
        org_id,
        details=f"Deleted organization: {org.name}",
        request=request,
    )
    await db.delete(org)
