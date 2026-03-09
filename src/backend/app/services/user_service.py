"""
User service — user profile and application business logic.

Public API:
    get_profile(user_id)                    — fetch User + UserProfile
    update_profile(user_id, data)           — partial update UserProfile fields
    get_applications(user_id, page, per)    — paginated list of user's applications
    apply_to_job(user_id, job_id)           — create a new application row
    withdraw_application(user_id, app_id)  — set application status → 'withdrawn'
    get_all_users(page, per_page)           — admin: paginated user list
    update_user_status(user_id, status)     — admin: change user status

All functions raise ValueError with an ErrorCode constant on failure so the
route layer can map it cleanly to the right HTTP status without leaking details.
"""
from sqlalchemy import update as sa_update
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.job import JobVacancy, UserJobApplication
from app.models.user import User, UserProfile
from app.utils.constants import ApplicationStatus, ErrorCode, JobStatus, UserStatus
from app.utils.helpers import paginate


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

def get_profile(user_id: str) -> tuple:
    """
    Return (User, UserProfile) for the given user_id.

    Raises:
        ValueError(ErrorCode.NOT_FOUND_USER) if user doesn't exist or is inactive.
    """
    user = db.session.get(User, user_id)
    if not user or user.status in UserStatus.INACTIVE:
        raise ValueError(ErrorCode.NOT_FOUND_USER)

    # Profile is always created at registration; guard in case it's missing.
    if not user.profile:
        profile = UserProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()

    return user, user.profile


def update_phone(user_id: str, phone: str) -> User:
    """
    Update the phone number on the User row.

    Raises:
        ValueError(ErrorCode.NOT_FOUND_USER) if user doesn't exist.
    """
    user = db.session.get(User, user_id)
    if not user or user.status in UserStatus.INACTIVE:
        raise ValueError(ErrorCode.NOT_FOUND_USER)

    user.phone = phone
    db.session.commit()
    return user


def update_profile(user_id: str, data: dict) -> tuple:
    """
    Apply non-None fields from UpdateProfileSchema output to UserProfile.

    Raises:
        ValueError(ErrorCode.NOT_FOUND_USER) if user doesn't exist.
    """
    user, profile = get_profile(user_id)

    _PROFILE_FIELDS = (
        'date_of_birth', 'gender', 'category', 'is_pwd', 'is_ex_serviceman',
        'state', 'city', 'pincode', 'highest_qualification',
        'education', 'physical_details', 'notification_preferences',
    )
    for field in _PROFILE_FIELDS:
        value = data.get(field)
        if value is not None:
            setattr(profile, field, value)

    db.session.commit()
    return user, profile


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

def get_applications(user_id: str, page: int = 1, per_page: int = 20) -> dict:
    """
    Return paginate() dict of UserJobApplication rows for a user,
    ordered by most recently applied first.
    """
    query = (
        UserJobApplication.query
        .filter_by(user_id=user_id)
        .order_by(UserJobApplication.applied_on.desc())
    )
    return paginate(query, page=page, per_page=per_page)


def apply_to_job(user_id: str, job_id: str) -> UserJobApplication:
    """
    Record that the user has applied to a job.

    Increments JobVacancy.applications_count on success.

    Raises:
        ValueError(ErrorCode.NOT_FOUND_JOB)         — job not found or not active.
        ValueError('ALREADY_APPLIED')               — duplicate application.
    """
    job = db.session.get(JobVacancy, job_id)
    if not job or job.status != JobStatus.ACTIVE:
        raise ValueError(ErrorCode.NOT_FOUND_JOB)

    # Enforce vacancy quota: reject applications once all slots are filled.
    if job.total_vacancies is not None and job.applications_count >= job.total_vacancies:
        raise ValueError(ErrorCode.JOB_FULL)

    application = UserJobApplication(user_id=user_id, job_id=job_id)
    db.session.add(application)

    # Atomic server-side increment avoids lost updates under concurrent requests.
    db.session.execute(
        sa_update(JobVacancy)
        .where(JobVacancy.id == job_id)
        .values(applications_count=JobVacancy.applications_count + 1)
    )
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ValueError(ErrorCode.ALREADY_APPLIED)
    return application


def withdraw_application(user_id: str, app_id: str) -> UserJobApplication:
    """
    Set application status to 'withdrawn'.

    Only the owning user can withdraw their own application.
    Applications already withdrawn are a no-op (idempotent).

    Raises:
        ValueError(ErrorCode.NOT_FOUND_APPLICATION) — not found or not owned by user.
    """
    application = UserJobApplication.query.filter_by(
        id=app_id, user_id=user_id
    ).first()
    if not application:
        raise ValueError(ErrorCode.NOT_FOUND_APPLICATION)

    if application.status != ApplicationStatus.WITHDRAWN:
        application.status = ApplicationStatus.WITHDRAWN

        # Atomic server-side decrement; only decrements when count is already > 0.
        db.session.execute(
            sa_update(JobVacancy)
            .where(JobVacancy.id == application.job_id, JobVacancy.applications_count > 0)
            .values(applications_count=JobVacancy.applications_count - 1)
        )
        db.session.commit()

    return application


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

def get_all_users(page: int = 1, per_page: int = 50) -> dict:
    """
    Return paginate() dict of all users ordered by creation date (newest first).
    Admin-only operation — caller is responsible for enforcing the role check.
    """
    query = User.query.order_by(User.created_at.desc())
    return paginate(query, page=page, per_page=per_page)


def update_user_status(user_id: str, status: str) -> User:
    """
    Change a user's status (active / suspended / deleted).

    Raises:
        ValueError(ErrorCode.NOT_FOUND_USER)             — user not found.
        ValueError(ErrorCode.VALIDATION_INVALID_FORMAT)  — status not in UserStatus.ALL.
    """
    if status not in UserStatus.ALL:
        raise ValueError(ErrorCode.VALIDATION_INVALID_FORMAT)

    user = db.session.get(User, user_id)
    if not user:
        raise ValueError(ErrorCode.NOT_FOUND_USER)

    user.status = status
    db.session.commit()
    return user
