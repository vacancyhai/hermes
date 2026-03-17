"""
Notification service — create, query, and update user notifications.

Public API:
    create_notification(user_id, type, title, message, ...)  — insert a new row
    get_notifications(user_id, page, per_page)               — paginated list
    mark_read(notification_id, user_id)                      — mark single as read
    mark_all_read(user_id)                                   — bulk read
    delete_notification(notification_id, user_id)            — hard delete
    match_job_to_users(job)                                  — returns list of (user_id, notification payload)
                                                               used by notification_tasks

All functions raise custom exceptions (NotFoundError, ValidationError, etc.)
which are automatically converted to appropriate HTTP responses by the error handler middleware.
"""
from datetime import datetime, timezone
import logging
from uuid import UUID

from app.extensions import db
from app.middleware.error_handler import NotFoundError, ValidationError
from app.models.notification import Notification
from app.models.user import User, UserProfile
from app.utils.constants import ErrorCode, NotificationType
from app.utils.helpers import paginate


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

def create_notification(
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    entity_type: str = None,
    entity_id: str = None,
    action_url: str = None,
    priority: str = "medium",
    commit: bool = True,
) -> Notification:
    """
    Insert a new notification row for `user_id`.

    When commit=False the row is flushed (ID assigned) but the transaction is
    left open so the caller can enqueue dependent tasks before committing.
    This prevents orphaned notifications when broker enqueue fails after commit.

    Returns the saved Notification instance.
    """
    entity_uuid = None
    if entity_id:
        try:
            entity_uuid = UUID(entity_id)
        except ValueError:
            raise ValidationError(f"Invalid entity ID format")

    notif = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        entity_type=entity_type,
        entity_id=entity_uuid,
        action_url=action_url,
        priority=priority,
    )
    db.session.add(notif)
    if commit:
        db.session.commit()
    else:
        db.session.flush()  # assigns the primary key without committing
    return notif


def mark_read(notification_id: str, user_id: str) -> Notification:
    """
    Mark a single notification as read.

    Raises:
        ValueError(ErrorCode.NOT_FOUND_...) if not found or does not belong to the user.
    """
    notif = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if not notif:
        raise ValueError(ErrorCode.NOT_FOUND_NOTIFICATION)

    if not notif.is_read:
        notif.is_read = True
        notif.read_at = datetime.now(timezone.utc)
        db.session.commit()
    return notif


def mark_all_read(user_id: str) -> int:
    """
    Mark every unread notification for `user_id` as read.

    Returns the number of rows updated.
    """
    now = datetime.now(timezone.utc)
    updated = (
        Notification.query
        .filter_by(user_id=user_id, is_read=False)
        .update({"is_read": True, "read_at": now}, synchronize_session=False)
    )
    db.session.commit()
    return updated


def delete_notification(notification_id: str, user_id: str) -> None:
    """
    Hard-delete a notification.

    Raises:
        ValueError if not found or does not belong to the user.
    """
    notif = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if not notif:
        raise ValueError(ErrorCode.NOT_FOUND_NOTIFICATION)
    db.session.delete(notif)
    db.session.commit()


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def get_notifications(user_id: str, page: int = 1, per_page: int = 20) -> dict:
    """
    Return a paginate() dict of notifications for `user_id`, newest first.
    """
    query = (
        Notification.query
        .filter_by(user_id=user_id)
        .order_by(Notification.created_at.desc())
    )
    return paginate(query, page=page, per_page=per_page)


def get_unread_count(user_id: str) -> int:
    """Return the count of unread notifications for `user_id`."""
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()


# ---------------------------------------------------------------------------
# Job matching
# ---------------------------------------------------------------------------

_MATCH_CHUNK_SIZE = 500
# Safety cap: with 500 users/chunk this covers 100 000 users per notification run.
_MAX_MATCH_PAGES = 200

_logger = logging.getLogger(__name__)


def match_job_to_users(job) -> list[dict]:
    """
    Find all active users whose profile is eligible for `job`.

    Eligibility rules (all must pass):
      1. User status == 'active'
      2. qualification_level: user's highest_qualification >= job's required level
      3. category vacancy: user's category is listed in job.eligibility.category_vacancies
      4. notification_preferences: user has not disabled this job_type
      5. age_limit: user's age at application_end is within job.eligibility.age_limit
                   {min_age: int, max_age: int} — skipped if job doesn't set this
      6. gender: job.eligibility.gender (e.g. "Male") must match profile.gender
                 — skipped if job doesn't restrict gender
      7. domicile: profile.state must be in job.eligibility.domicile_states list
                   — skipped if job doesn't restrict domicile
      8. ex_serviceman_only: job.eligibility.ex_serviceman_only == True requires
                             profile.is_ex_serviceman == True
      9. pwd_only: job.eligibility.pwd_only == True requires profile.is_pwd == True

    Users are fetched in chunks of _MATCH_CHUNK_SIZE to avoid loading the full
    user table into memory at once.

    Returns a list of dicts:
        [{"user_id": str, "email": str, "full_name": str}, ...]
    """
    from datetime import date
    from app.utils.constants import UserStatus

    eligible: list[dict] = []

    job_qual = getattr(job, "qualification_level", None)
    job_eligibility = getattr(job, "eligibility", {}) or {}
    job_type = getattr(job, "job_type", None)
    # Use application_end as the reference date for age calculations
    age_ref_date = getattr(job, "application_end", None) or date.today()

    # Pre-extract eligibility fields once (avoids repeated dict lookups per user)
    age_limit = job_eligibility.get("age_limit") or {}
    min_age = age_limit.get("min_age")
    max_age = age_limit.get("max_age")
    required_gender = job_eligibility.get("gender")           # e.g. "Male", "Female", None
    domicile_states = job_eligibility.get("domicile_states")  # list of state names, or None
    ex_serviceman_only = bool(job_eligibility.get("ex_serviceman_only", False))
    pwd_only = bool(job_eligibility.get("pwd_only", False))
    category_vacancies = job_eligibility.get("category_vacancies", {})

    offset = 0
    pages_fetched = 0
    while True:
        if pages_fetched >= _MAX_MATCH_PAGES:
            _logger.warning(
                "match_job_to_users: page limit (%d) reached for job %s; "
                "stopping after ~%d users matched.",
                _MAX_MATCH_PAGES, getattr(job, 'id', '?'), len(eligible),
            )
            break
        rows = (
            db.session.query(User, UserProfile)
            .join(UserProfile, UserProfile.user_id == User.id)
            .filter(User.status == UserStatus.ACTIVE)
            .order_by(User.id)
            .limit(_MATCH_CHUNK_SIZE)
            .offset(offset)
            .all()
        )
        if not rows:
            break

        for user, profile in rows:
            # 1. Qualification check
            if job_qual and profile.highest_qualification:
                if not _qualification_meets(profile.highest_qualification, job_qual):
                    continue

            # 2. Category vacancy check
            if category_vacancies and profile.category:
                if profile.category not in category_vacancies:
                    continue

            # 3. Notification preference check — user may have opted out of a job_type
            prefs = profile.notification_preferences or {}
            disabled_types = prefs.get("disabled_job_types", [])
            if job_type and job_type in disabled_types:
                continue

            # 4. Age range check (only if job specifies min or max age)
            if (min_age is not None or max_age is not None) and profile.date_of_birth:
                user_age = _age_at(profile.date_of_birth, age_ref_date)
                if min_age is not None and user_age < min_age:
                    continue
                if max_age is not None and user_age > max_age:
                    continue

            # 5. Gender check (only if job restricts gender)
            if required_gender and profile.gender:
                if profile.gender.lower() != required_gender.lower():
                    continue

            # 6. Domicile/state check (only if job restricts to specific states)
            if domicile_states and profile.state:
                if profile.state not in domicile_states:
                    continue

            # 7. Ex-serviceman only check
            if ex_serviceman_only and not profile.is_ex_serviceman:
                continue

            # 8. PWD only check
            if pwd_only and not profile.is_pwd:
                continue

            eligible.append({
                "user_id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
            })

        pages_fetched += 1
        offset += len(rows)

    return eligible


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

_QUAL_RANK = {
    "10th": 1,
    "12th": 2,
    "diploma": 3,
    "graduate": 4,
    "postgraduate": 5,
    "doctorate": 6,
}


def _qualification_meets(user_qual: str, required_qual: str) -> bool:
    """Return True if user's qualification is >= required."""
    user_rank = _QUAL_RANK.get(user_qual.lower(), 0)
    req_rank = _QUAL_RANK.get(required_qual.lower(), 0)
    return user_rank >= req_rank


def _age_at(date_of_birth, reference_date) -> int:
    """Return age in whole years at reference_date."""
    from datetime import date as _date
    if isinstance(reference_date, _date):
        ref = reference_date
    else:
        ref = reference_date.date() if hasattr(reference_date, 'date') else _date.today()
    dob = date_of_birth if isinstance(date_of_birth, _date) else date_of_birth
    age = ref.year - dob.year - ((ref.month, ref.day) < (dob.month, dob.day))
    return age
