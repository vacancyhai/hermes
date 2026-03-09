"""
Job view-count flush task — scheduled via Celery Beat (every 5 minutes).

How it works:
    1. Every time a user visits GET /api/v1/jobs/<slug>, job_service
       increments a Redis counter at key "job:views:<job_id>" instead of
       writing to PostgreSQL on every request.
    2. This task runs periodically, reads every "job:views:*" key in Redis,
       applies the accumulated delta to the JobVacancy.views column, then
       deletes the Redis keys only after a successful DB commit.

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

    Reads all view counters first (MGET), commits them to DB, then deletes
    the Redis keys. This ordering ensures counts are never lost: if the DB
    commit fails the keys remain in Redis and will be picked up next cycle.

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

    # Read all values before touching the DB — keys stay in Redis until commit succeeds
    raw_values = redis_client.mget(keys)

    jobs_updated = 0
    total_views = 0
    committed_keys = []

    for key, raw in zip(keys, raw_values):
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
        if isinstance(job_id, bytes):
            job_id = job_id.decode()

        job = db.session.get(JobVacancy, job_id)
        if not job:
            logger.debug("flush_job_views: job %s not found, discarding %d views", job_id, delta)
            # Key is stale — safe to delete even without a DB update
            committed_keys.append(key)
            continue

        job.views = (job.views or 0) + delta
        jobs_updated += 1
        total_views += delta
        committed_keys.append(key)

    if jobs_updated:
        try:
            db.session.commit()
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.error("flush_job_views: DB commit failed — view counts preserved in Redis: %s", exc)
            return {"jobs_updated": 0, "total_views_flushed": 0}

    # Delete keys only after a successful commit so counts survive failures
    if committed_keys:
        redis_client.delete(*committed_keys)

    logger.info(
        "flush_job_views: jobs_updated=%d total_views_flushed=%d",
        jobs_updated, total_views,
    )
    return {"jobs_updated": jobs_updated, "total_views_flushed": total_views}
