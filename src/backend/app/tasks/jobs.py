"""Job-related Celery tasks.

Scheduled:
  close_expired_job_listings  — Daily 02:30 UTC
  update_exam_statuses        — Daily 02:35 UTC
"""

import logging

from app.celery_app import celery
from app.database import sync_engine
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@celery.task(
    name="app.tasks.jobs.close_expired_job_listings",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def close_expired_job_listings(self):
    """Mark jobs past application_end as 'expired'. Daily 02:30 UTC.

    Uses 'expired' (not 'cancelled') so deadline-lapsed jobs are distinct
    from manually soft-deleted jobs and are not purged by purge_soft_deleted_jobs.
    """
    try:
        with Session(sync_engine) as session:
            result = session.execute(
                text(
                    """
                    UPDATE jobs
                    SET status = 'expired', updated_at = NOW()
                    WHERE status = 'active'
                      AND application_end IS NOT NULL
                      AND application_end < CURRENT_DATE
                    RETURNING id
                """
                )
            )
            expired_ids = [str(row[0]) for row in result.fetchall()]
            session.commit()
    except Exception as exc:
        logger.error(f"close_expired_job_listings failed: {exc}")
        raise self.retry(exc=exc)

    logger.info(f"Marked {len(expired_ids)} job listings as expired")
    return {"closed_count": len(expired_ids)}


@celery.task(
    name="app.tasks.jobs.update_exam_statuses",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def update_exam_statuses(self):
    """Mark admissions as 'completed' after exam_date passes. Daily 02:35 UTC."""
    try:
        with Session(sync_engine) as session:
            result = session.execute(
                text(
                    """
                    UPDATE admissions
                    SET status = 'completed', updated_at = NOW()
                    WHERE status = 'active'
                      AND exam_date IS NOT NULL
                      AND exam_date < CURRENT_DATE
                    RETURNING id
                """
                )
            )
            completed_ids = [str(row[0]) for row in result.fetchall()]
            session.commit()
    except Exception as exc:
        logger.error(f"update_exam_statuses failed: {exc}")
        raise self.retry(exc=exc)

    logger.info(f"Marked {len(completed_ids)} admissions as completed")
    return {"completed_count": len(completed_ids)}
