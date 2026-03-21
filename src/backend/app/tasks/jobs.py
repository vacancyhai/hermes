"""Job-related Celery tasks."""

from app.celery_app import celery


@celery.task(name="app.tasks.jobs.close_expired_job_listings")
def close_expired_job_listings():
    """Auto-close jobs past application_end. Daily 02:30 UTC. TODO: Implement."""
    pass
