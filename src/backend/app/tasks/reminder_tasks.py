"""
Deadline reminder Celery tasks — scheduled via Celery Beat.

Tasks defined here:
    send_deadline_reminders()
        — Cron task (run daily at 08:00 UTC).
          Finds all jobs whose application_end is exactly 7, 3, or 1 day
          from today, then emails every user who has applied to that job.

The task is registered in celery_app.beat_schedule in celery_app.py
(or can be configured via django-celery-beat / redbeat).
"""
import logging
from datetime import datetime, timedelta, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

# Remind at these many days before the application closes.
_REMINDER_DAYS = (7, 3, 1)


@celery_app.task(name="reminder_tasks.send_deadline_reminders")
def send_deadline_reminders() -> dict:
    """
    Send application-deadline reminder emails.

    Iterates over the three reminder thresholds (7d / 3d / 1d).
    For each threshold, fetches jobs whose application_end == today + N days,
    then emails every user who has tracked that job.

    Returns a summary dict: {"thresholds_processed": int, "emails_sent": int}
    """
    from app.extensions import db
    from app.models.job import JobVacancy, UserJobApplication
    from app.models.user import User, UserProfile
    from app.services.email_service import send_deadline_reminder_email
    from app.utils.constants import ApplicationStatus, JobStatus, UserStatus

    today = datetime.now(timezone.utc).date()
    emails_sent = 0

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

                try:
                    send_deadline_reminder_email(
                        to_email=user.email,
                        full_name=user.full_name,
                        job_title=job.job_title,
                        organization=job.organization,
                        days_left=days_left,
                        application_end=str(job.application_end),
                        job_url=f"/jobs/{job.slug}",
                    )
                    emails_sent += 1
                except Exception as exc:
                    logger.error(
                        "send_deadline_reminders: failed for user=%s job=%s: %s",
                        user.id, job.id, exc,
                    )

    logger.info("send_deadline_reminders: emails_sent=%d", emails_sent)
    return {"thresholds_processed": len(_REMINDER_DAYS), "emails_sent": emails_sent}
