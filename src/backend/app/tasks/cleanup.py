"""Cleanup Celery tasks — purge expired records."""

from app.celery_app import celery
from app.database import sync_engine
from sqlalchemy import text


def _execute_cleanup(stmt_text: str) -> int:
    """Execute a DELETE statement synchronously and return rows affected."""
    with sync_engine.connect() as conn:
        result = conn.execute(text(stmt_text))
        conn.commit()
        return result.rowcount


@celery.task(name="app.tasks.cleanup.purge_expired_notifications")
def purge_expired_notifications():
    """Delete notifications past expires_at. Daily 01:00 UTC."""
    count = _execute_cleanup(
        "DELETE FROM notifications WHERE expires_at IS NOT NULL AND expires_at < NOW()"
    )
    return {"purged_notifications": count}


@celery.task(name="app.tasks.cleanup.purge_expired_admin_logs")
def purge_expired_admin_logs():
    """Delete admin logs past expires_at. Daily 01:30 UTC."""
    count = _execute_cleanup(
        "DELETE FROM admin_logs WHERE expires_at IS NOT NULL AND expires_at < NOW()"
    )
    return {"purged_admin_logs": count}


@celery.task(name="app.tasks.cleanup.purge_soft_deleted_jobs")
def purge_soft_deleted_jobs():
    """Hard-delete jobs soft-deleted > 90 days ago. Daily 02:00 UTC."""
    count = _execute_cleanup(
        "DELETE FROM jobs WHERE status = 'cancelled' "
        "AND updated_at < NOW() - INTERVAL '90 days'"
    )
    return {"purged_jobs": count}
