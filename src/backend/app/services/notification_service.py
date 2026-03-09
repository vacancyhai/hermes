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

All functions raise ValueError on bad input so the route layer can map
to the correct HTTP status without leaking internals.
"""
from datetime import datetime, timezone
from uuid import UUID

from app.extensions import db
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
) -> Notification:
    """
    Insert a new notification row for `user_id`.

    Returns the saved Notification instance.
    """
    entity_uuid = None
    if entity_id:
        try:
            entity_uuid = UUID(entity_id)
        except ValueError:
            raise ValueError(f"Invalid entity_id: {entity_id!r} is not a valid UUID")

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
    db.session.commit()
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


def match_job_to_users(job) -> list[dict]:
    """
    Find all active users whose profile is eligible for `job`.

    Eligibility rules (all must pass):
      1. User status == 'active'
      2. qualification_level matches profile.highest_qualification (if job specifies one)
      3. category vacancy available for profile.category (if job.eligibility has category_vacancies)
      4. User notification_preferences does not explicitly exclude this job_type

    Users are fetched in chunks of _MATCH_CHUNK_SIZE to avoid loading the full
    user table into memory at once.

    Returns a list of dicts:
        [{"user_id": str, "email": str, "full_name": str}, ...]
    """
    from app.models.user import User, UserProfile
    from app.utils.constants import UserStatus

    eligible: list[dict] = []

    job_qual = getattr(job, "qualification_level", None)
    job_eligibility = getattr(job, "eligibility", {}) or {}
    job_type = getattr(job, "job_type", None)

    offset = 0
    while True:
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
            category_vacancies = job_eligibility.get("category_vacancies", {})
            if category_vacancies and profile.category:
                if profile.category not in category_vacancies:
                    continue

            # 3. Notification preference check — user may have opted out of a job_type
            prefs = profile.notification_preferences or {}
            disabled_types = prefs.get("disabled_job_types", [])
            if job_type and job_type in disabled_types:
                continue

            eligible.append({
                "user_id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
            })

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
