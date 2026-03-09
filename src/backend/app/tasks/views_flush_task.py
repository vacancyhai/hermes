"""
Job view-count flush task — scheduled via Celery Beat (every 5 minutes).

How it works:
    1. Every time a user visits GET /api/v1/jobs/<slug>, job_service
       increments a Redis counter at key "job:views:<job_id>" instead of
       writing to PostgreSQL on every request.
    2. This task runs periodically, reads every "job:views:*" key in Redis,
       applies the accumulated delta to the JobVacancy.views column, and
       deletes the Redis key atomically.

This approach trades a small amount of accuracy (±5 min lag) for a
significant reduction in write amplification on the jobs table.
"""
import logging

from sqlalchemy.exc import SQLAlchemyError

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

_VIEWS_KEY_PREFIX = "job:views:"


@celery_app.task(name="views_flush_task.flush_job_views")
def flush_job_views() -> dict:
    """
    Flush buffered view counts from Redis into PostgreSQL.

    Uses GETDEL to read and clear each counter atomically. Note: counts
    removed from Redis before a failed DB commit are lost for that cycle.
    For a view counter this is an acceptable trade-off; the remaining jobs
    are still committed.

    Returns:
        {"jobs_updated": int, "total_views_flushed": int}
    """
    from flask import current_app
    from app.extensions import db
    from app.models.job import JobVacancy

    redis_client = current_app.redis
    pattern = f"{_VIEWS_KEY_PREFIX}*"

    # Scan for all buffered view keys
    keys = list(redis_client.scan_iter(pattern))
    if not keys:
        return {"jobs_updated": 0, "total_views_flushed": 0}

    jobs_updated = 0
    total_views = 0

    for key in keys:
        # GETDEL atomically returns the current value and removes the key.
        # If the key was already deleted between scan and here, value is None.
        raw = redis_client.getdel(key)
        if raw is None:
            continue

        try:
            delta = int(raw)
        except (ValueError, TypeError):
            logger.warning("flush_job_views: unexpected value for key %s: %r", key, raw)
            continue

        if delta <= 0:
            continue

        job_id = key[len(_VIEWS_KEY_PREFIX):]

        job = db.session.get(JobVacancy, job_id)
        if not job:
            logger.debug("flush_job_views: job %s not found, discarding %d views", job_id, delta)
            continue

        job.views = (job.views or 0) + delta
        jobs_updated += 1
        total_views += delta

    if jobs_updated:
        try:
            db.session.commit()
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("flush_job_views: DB commit failed: %s", exc)
            return {"jobs_updated": 0, "total_views_flushed": 0}

    logger.info(
        "flush_job_views: jobs_updated=%d total_views_flushed=%d",
        jobs_updated, total_views,
    )
    return {"jobs_updated": jobs_updated, "total_views_flushed": total_views}
