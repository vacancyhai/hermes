"""Job-related Celery tasks.

Scheduled:
  close_expired_job_listings  — Daily 02:30 UTC
  update_admission_statuses        — Daily 02:35 UTC
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
    """Mark jobs past application_end as 'closed'. Daily 02:30 UTC."""
    try:
        with Session(sync_engine) as session:
            result = session.execute(
                text(
                    """
                    UPDATE jobs
                    SET status = 'closed', updated_at = NOW()
                    WHERE status = 'active'
                      AND application_end IS NOT NULL
                      AND application_end < CURRENT_DATE
                    RETURNING id
                """
                )
            )
            closed_ids = [str(row[0]) for row in result.fetchall()]
            session.commit()
    except Exception as exc:
        logger.error(f"close_expired_job_listings failed: {exc}")
        raise self.retry(exc=exc)

    logger.info(f"Marked {len(closed_ids)} job listings as closed")
    return {"closed_count": len(closed_ids)}


@celery.task(
    name="app.tasks.jobs.update_admission_statuses",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def update_admission_statuses(self):
    """Mark admissions as 'closed' after admission_date passes. Daily 02:35 UTC."""
    try:
        with Session(sync_engine) as session:
            result = session.execute(
                text(
                    """
                    UPDATE admissions
                    SET status = 'closed', updated_at = NOW()
                    WHERE status = 'active'
                      AND admission_date IS NOT NULL
                      AND admission_date < CURRENT_DATE
                    RETURNING id
                """
                )
            )
            closed_ids = [str(row[0]) for row in result.fetchall()]
            session.commit()
    except Exception as exc:
        logger.error(f"update_admission_statuses failed: {exc}")
        raise self.retry(exc=exc)

    logger.info(f"Marked {len(closed_ids)} admissions as closed")
    return {"closed_count": len(closed_ids)}
