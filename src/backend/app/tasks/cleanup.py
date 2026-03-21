"""Cleanup Celery tasks — purge expired records."""

from app.celery_app import celery


@celery.task(name="app.tasks.cleanup.purge_expired_notifications")
def purge_expired_notifications():
    """Delete notifications past expires_at. Daily 01:00 UTC. TODO: Implement."""
    pass


@celery.task(name="app.tasks.cleanup.purge_expired_admin_logs")
def purge_expired_admin_logs():
    """Delete admin logs past expires_at. Daily 01:30 UTC. TODO: Implement."""
    pass


@celery.task(name="app.tasks.cleanup.purge_soft_deleted_jobs")
def purge_soft_deleted_jobs():
    """Hard-delete jobs soft-deleted > 90 days ago. Daily 02:00 UTC. TODO: Implement."""
    pass
