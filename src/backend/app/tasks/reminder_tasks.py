"""
Deadline reminder Celery tasks — scheduled via Celery Beat.

Tasks defined here:
    send_deadline_reminders()
        — Cron task (run daily at 08:00 UTC).
          Finds all jobs whose application_end is exactly 7, 3, or 1 day
          from today, then queues a deliver_deadline_reminder_email subtask
          for each eligible user so individual failures retry independently.

    deliver_deadline_reminder_email(...)
        — Delivers a single reminder email with exponential-backoff retry.

The task is registered in celery_app.beat_schedule in celery_app.py
(or can be configured via django-celery-beat / redbeat).
"""
import logging
from datetime import datetime, timedelta, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

# Remind at these many days before the application closes.
_REMINDER_DAYS = (7, 3, 1)

_MAX_RETRIES = 5
_RETRY_BACKOFF = (1, 2, 4, 8, 16)   # seconds between retries


@celery_app.task(name="reminder_tasks.send_deadline_reminders")
def send_deadline_reminders() -> dict:
    """
    Queue application-deadline reminder emails.

    Iterates over the three reminder thresholds (7d / 3d / 1d).
    For each threshold, fetches jobs whose application_end == today + N days,
    then queues a deliver_deadline_reminder_email subtask per eligible user.
    Each subtask retries independently so one failure doesn't affect others.

    Returns a summary dict: {"thresholds_processed": int, "emails_queued": int}
    """
    from app.extensions import db
    from app.models.job import JobVacancy, UserJobApplication
    from app.models.user import User, UserProfile
    from app.utils.constants import ApplicationStatus, JobStatus, UserStatus

    today = datetime.now(timezone.utc).date()
    emails_queued = 0

    for days_left in _REMINDER_DAYS:
        target_date = today + timedelta(days=days_left)

        # Jobs that close exactly `days_left` days from now
        jobs = (
            JobVacancy.query
            .filter(
                JobVacancy.application_end == target_date,
                JobVacancy.status == JobStatus.ACTIVE,
            )
            .all()
        )

        for job in jobs:
            # Join User and UserProfile into the applications query to avoid N+1
            rows = (
                db.session.query(UserJobApplication, User, UserProfile)
                .join(User, User.id == UserJobApplication.user_id)
                .outerjoin(UserProfile, UserProfile.user_id == User.id)
                .filter(
                    UserJobApplication.job_id == job.id,
                    UserJobApplication.status != ApplicationStatus.WITHDRAWN,
                    User.status == UserStatus.ACTIVE,
                )
                .all()
            )

            for application, user, profile in rows:
                # Respect per-user reminder preference
                if profile:
                    prefs = profile.notification_preferences or {}
                    if not prefs.get("email_reminders", True):
                        continue

                deliver_deadline_reminder_email.delay(
                    to_email=user.email,
                    full_name=user.full_name,
                    job_title=job.job_title,
                    organization=job.organization,
                    days_left=days_left,
                    application_end=str(job.application_end),
                    job_url=f"/jobs/{job.slug}",
                )
                emails_queued += 1

    logger.info("send_deadline_reminders: emails_queued=%d", emails_queued)
    return {"thresholds_processed": len(_REMINDER_DAYS), "emails_queued": emails_queued}


@celery_app.task(bind=True, max_retries=_MAX_RETRIES, name="reminder_tasks.deliver_deadline_reminder_email")
def deliver_deadline_reminder_email(
    self,
    to_email: str,
    full_name: str,
    job_title: str,
    organization: str,
    days_left: int,
    application_end: str,
    job_url: str,
) -> None:
    """
    Send a single deadline reminder email with exponential-backoff retry.
    """
    from app.services.email_service import send_deadline_reminder_email

    try:
        send_deadline_reminder_email(
            to_email=to_email,
            full_name=full_name,
            job_title=job_title,
            organization=organization,
            days_left=days_left,
            application_end=application_end,
            job_url=job_url,
        )
        logger.info("deliver_deadline_reminder_email: sent to %s for job %r", to_email, job_title)
    except Exception as exc:
        retry_index = min(self.request.retries, len(_RETRY_BACKOFF) - 1)
        countdown = _RETRY_BACKOFF[retry_index]
        logger.warning(
            "deliver_deadline_reminder_email: failed for %s (attempt %d), retrying in %ds: %s",
            to_email, self.request.retries + 1, countdown, exc,
        )
        raise self.retry(exc=exc, countdown=countdown)
