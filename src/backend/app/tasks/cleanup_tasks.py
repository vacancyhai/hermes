"""
Cleanup Celery tasks — scheduled via Celery Beat (run daily).

Tasks defined here:
    purge_expired_notifications()
        — Delete Notification rows whose expires_at < NOW().

    purge_expired_admin_logs()
        — Delete AdminLog rows whose expires_at < NOW().

    purge_soft_deleted_jobs()
        — Hard-delete JobVacancy rows that have been soft-deleted
          (status == 'archived') for more than 90 days.

    close_expired_job_listings()
        — Set any active job whose application_end < today to status='closed'.
"""
import logging
from datetime import datetime, date, timedelta, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="cleanup_tasks.purge_expired_notifications")
def purge_expired_notifications() -> dict:
    """Delete notifications past their expires_at TTL."""
    from app.extensions import db
    from app.models.notification import Notification
    from sqlalchemy import text

    now = datetime.now(timezone.utc)
    deleted = (
        db.session.query(Notification)
        .filter(Notification.expires_at < now)
        .delete(synchronize_session=False)
    )
    db.session.commit()
    logger.info("purge_expired_notifications: deleted=%d", deleted)
    return {"deleted": deleted}


@celery_app.task(name="cleanup_tasks.purge_expired_admin_logs")
def purge_expired_admin_logs() -> dict:
    """Delete AdminLog rows past their expires_at TTL."""
    from app.extensions import db
    from app.models.admin import AdminLog

    now = datetime.now(timezone.utc)
    deleted = (
        db.session.query(AdminLog)
        .filter(AdminLog.expires_at < now)
        .delete(synchronize_session=False)
    )
    db.session.commit()
    logger.info("purge_expired_admin_logs: deleted=%d", deleted)
    return {"deleted": deleted}


@celery_app.task(name="cleanup_tasks.purge_soft_deleted_jobs")
def purge_soft_deleted_jobs() -> dict:
    """
    Hard-delete jobs that have been in status='archived' for more than 90 days.

    The cutoff is: updated_at < 90 days ago AND status == 'archived'.
    """
    from app.extensions import db
    from app.models.job import JobVacancy
    from app.utils.constants import JobStatus

    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    deleted = (
        db.session.query(JobVacancy)
        .filter(
            JobVacancy.status == JobStatus.ARCHIVED,
            JobVacancy.updated_at < cutoff,
        )
        .delete(synchronize_session=False)
    )
    db.session.commit()
    logger.info("purge_soft_deleted_jobs: deleted=%d", deleted)
    return {"deleted": deleted}


@celery_app.task(name="cleanup_tasks.close_expired_job_listings")
def close_expired_job_listings() -> dict:
    """
    Set status='closed' on active jobs whose application_end < today.
    """
    from app.extensions import db
    from app.models.job import JobVacancy
    from app.utils.constants import JobStatus

    today = date.today()
    updated = (
        db.session.query(JobVacancy)
        .filter(
            JobVacancy.status == JobStatus.ACTIVE,
            JobVacancy.application_end < today,
        )
        .update({"status": JobStatus.CLOSED}, synchronize_session=False)
    )
    db.session.commit()
    logger.info("close_expired_job_listings: updated=%d", updated)
    return {"closed": updated}
