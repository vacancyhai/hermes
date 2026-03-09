"""
Notification Celery tasks.

Tasks defined here:
    send_new_job_notifications(job_id)
        — Triggered when a new job vacancy is published.
          Fetches all eligible users, creates in-app Notification rows,
          and sends email alerts via email_service.

    deliver_notification(notification_id)
        — Sends a single queued notification (email + optional push).
          Called by send_new_job_notifications but can also be called
          directly for one-off notifications.

Both tasks retry up to 5 times with exponential backoff on failure.
"""
import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

_MAX_RETRIES = 5
_RETRY_BACKOFF = (1, 2, 4, 8, 16)   # seconds between retries


# ---------------------------------------------------------------------------
# Public tasks
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=_MAX_RETRIES, name="notification_tasks.send_new_job_notifications")
def send_new_job_notifications(self, job_id: str) -> dict:
    """
    Match a newly published job to all eligible users and create notifications.

    Args:
        job_id: UUID string of the JobVacancy row.

    Returns:
        {"matched": int, "created": int, "emails_queued": int}
    """
    from sqlalchemy.exc import OperationalError

    from app.extensions import db
    from app.models.job import JobVacancy
    from app.services.notification_service import create_notification, match_job_to_users
    from app.utils.constants import NotificationType

    try:
        job = db.session.get(JobVacancy, job_id)
    except OperationalError as exc:
        retry_index = min(self.request.retries, len(_RETRY_BACKOFF) - 1)
        logger.warning(
            "send_new_job_notifications: DB unavailable for job %s (attempt %d), retrying: %s",
            job_id, self.request.retries + 1, exc,
        )
        raise self.retry(exc=exc, countdown=_RETRY_BACKOFF[retry_index])

    if not job:
        logger.warning("send_new_job_notifications: job %s not found", job_id)
        return {"matched": 0, "created": 0, "emails_queued": 0}

    matched_users = match_job_to_users(job)
    created = 0
    emails_queued = 0

    app_end = str(job.application_end) if job.application_end else "N/A"
    action_url = f"/jobs/{job.slug}"

    for user_info in matched_users:
        try:
            notif = create_notification(
                user_id=user_info["user_id"],
                notification_type=NotificationType.NEW_JOB,
                title=f"New Job: {job.job_title}",
                message=(
                    f"{job.organization} has opened applications for "
                    f"'{job.job_title}'. Last date: {app_end}."
                ),
                entity_type="job_vacancy",
                entity_id=str(job.id),
                action_url=action_url,
                priority="high" if job.is_urgent else "medium",
            )
            created += 1

            # Queue the email delivery as a separate task so one failure
            # doesn't abort the entire batch. Pass notification_id so the task
            # can mark sent_via and skip re-delivery on retry.
            deliver_notification_email.delay(
                notification_id=str(notif.id),
                to_email=user_info["email"],
                full_name=user_info["full_name"],
                job_title=job.job_title,
                organization=job.organization,
                application_end=app_end,
                job_url=action_url,
            )
            emails_queued += 1

        except Exception as exc:
            logger.error(
                "send_new_job_notifications: failed for user %s: %s",
                user_info["user_id"],
                exc,
            )

    logger.info(
        "send_new_job_notifications: job=%s matched=%d created=%d emails=%d",
        job_id, len(matched_users), created, emails_queued,
    )
    return {"matched": len(matched_users), "created": created, "emails_queued": emails_queued}


@celery_app.task(bind=True, max_retries=_MAX_RETRIES, name="notification_tasks.deliver_notification_email")
def deliver_notification_email(
    self,
    notification_id: str,
    to_email: str,
    full_name: str,
    job_title: str,
    organization: str,
    application_end: str,
    job_url: str,
) -> None:
    """
    Send a job-alert email to a single user.

    Checks the notification's sent_via field before sending to ensure
    idempotency — if this task retries after a partial success, the email
    is not sent a second time.

    Retries up to 5 times with exponential backoff on SMTP failure.
    """
    from app.extensions import db
    from app.models.notification import Notification
    from app.services.email_service import send_job_notification_email

    # Idempotency check: skip if email was already delivered
    notif = db.session.get(Notification, notification_id)
    if notif and notif.sent_via and 'email' in (notif.sent_via or []):
        logger.info("deliver_notification_email: already sent to %s, skipping", to_email)
        return

    try:
        send_job_notification_email(
            to_email=to_email,
            full_name=full_name,
            job_title=job_title,
            organization=organization,
            application_end=application_end,
            job_url=job_url,
        )
        # Mark as sent so retries are idempotent
        if notif:
            notif.sent_via = list(notif.sent_via or []) + ['email']
            db.session.commit()
        logger.info("deliver_notification_email: sent to %s", to_email)
    except Exception as exc:
        retry_index = min(self.request.retries, len(_RETRY_BACKOFF) - 1)
        countdown = _RETRY_BACKOFF[retry_index]
        logger.warning(
            "deliver_notification_email: failed for %s (attempt %d), retrying in %ds: %s",
            to_email, self.request.retries + 1, countdown, exc,
        )
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(bind=True, max_retries=_MAX_RETRIES, name="notification_tasks.send_verification_email_task")
def send_verification_email_task(self, user_id: str, verify_token: str) -> None:
    """
    Send the email-verification link to a newly registered user.

    verify_token is stored in Redis (key email_verify:{token}).
    The full URL is constructed from FRONTEND_URL env var.
    """
    import os
    from app.extensions import db
    from app.models.user import User
    from app.services.email_service import send_verification_email

    user = db.session.get(User, user_id)
    if not user:
        return

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8080")
    verify_url = f"{frontend_url}/auth/verify-email?token={verify_token}"

    try:
        send_verification_email(user.email, user.full_name, verify_url)
    except Exception as exc:
        retry_index = min(self.request.retries, len(_RETRY_BACKOFF) - 1)
        raise self.retry(exc=exc, countdown=_RETRY_BACKOFF[retry_index])


@celery_app.task(bind=True, max_retries=_MAX_RETRIES, name="notification_tasks.send_password_reset_email_task")
def send_password_reset_email_task(self, user_id: str, reset_token: str) -> None:
    """
    Send the password-reset link generated by /auth/forgot-password.
    """
    import os
    from app.extensions import db
    from app.models.user import User
    from app.services.email_service import send_password_reset_email

    user = db.session.get(User, user_id)
    if not user:
        return

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8080")
    reset_url = f"{frontend_url}/auth/reset-password?token={reset_token}"

    try:
        send_password_reset_email(user.email, user.full_name, reset_url)
    except Exception as exc:
        retry_index = min(self.request.retries, len(_RETRY_BACKOFF) - 1)
        raise self.retry(exc=exc, countdown=_RETRY_BACKOFF[retry_index])
