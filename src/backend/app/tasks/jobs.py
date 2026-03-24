"""Job-related Celery tasks.

Scheduled:
  close_expired_job_listings  — Daily 02:30 UTC
  update_exam_statuses        — Daily 02:35 UTC

Event-driven:
  extract_job_from_pdf        — Process uploaded PDF → AI extraction → create draft job
"""

import logging
import os
import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.celery_app import celery
from app.database import sync_engine

logger = logging.getLogger(__name__)


@celery.task(name="app.tasks.jobs.close_expired_job_listings", bind=True, max_retries=3, default_retry_delay=60)
def close_expired_job_listings(self):
    """Mark jobs past application_end as 'expired'. Daily 02:30 UTC.

    Uses 'expired' (not 'cancelled') so deadline-lapsed jobs are distinct
    from manually soft-deleted jobs and are not purged by purge_soft_deleted_jobs.
    """
    try:
        with Session(sync_engine) as session:
            result = session.execute(
                text("""
                    UPDATE job_vacancies
                    SET status = 'expired', updated_at = NOW()
                    WHERE status = 'active'
                      AND application_end IS NOT NULL
                      AND application_end < CURRENT_DATE
                    RETURNING id
                """)
            )
            expired_ids = [str(row[0]) for row in result.fetchall()]
            session.commit()
    except Exception as exc:
        logger.error(f"close_expired_job_listings failed: {exc}")
        raise self.retry(exc=exc)

    logger.info(f"Marked {len(expired_ids)} job listings as expired")
    return {"expired_count": len(expired_ids)}


@celery.task(name="app.tasks.jobs.update_exam_statuses", bind=True, max_retries=3, default_retry_delay=60)
def update_exam_statuses(self):
    """Mark entrance exams as 'completed' after exam_date passes. Daily 02:35 UTC."""
    try:
        with Session(sync_engine) as session:
            result = session.execute(
                text("""
                    UPDATE entrance_exams
                    SET status = 'completed', updated_at = NOW()
                    WHERE status = 'active'
                      AND exam_date IS NOT NULL
                      AND exam_date < CURRENT_DATE
                    RETURNING id
                """)
            )
            completed_ids = [str(row[0]) for row in result.fetchall()]
            session.commit()
    except Exception as exc:
        logger.error(f"update_exam_statuses failed: {exc}")
        raise self.retry(exc=exc)

    logger.info(f"Marked {len(completed_ids)} entrance exams as completed")
    return {"completed_count": len(completed_ids)}


@celery.task(name="app.tasks.jobs.extract_job_from_pdf", bind=True, max_retries=2)
def extract_job_from_pdf(self, pdf_path: str, admin_id: str):
    """Process uploaded PDF: extract text → AI extraction → create draft job."""
    from app.services.pdf_extractor import extract_text_from_pdf
    from app.services.ai_extractor import extract_job_data

    # Step 1: Extract text from PDF
    try:
        pdf_text = extract_text_from_pdf(pdf_path)
    except Exception as e:
        logger.error(f"PDF text extraction failed: {e}")
        raise self.retry(exc=e, countdown=30)

    if not pdf_text.strip():
        logger.warning(f"PDF has no extractable text: {pdf_path}")
        try:
            os.unlink(pdf_path)
        except OSError:
            pass
        return {"status": "error", "detail": "PDF has no extractable text"}

    # Step 2: AI extraction
    extracted = extract_job_data(pdf_text)

    if not extracted:
        # Fallback: create draft with raw text as description
        extracted = {
            "job_title": f"Untitled — PDF Upload {pdf_path.split('/')[-1]}",
            "organization": "Unknown",
            "description": pdf_text[:2000],
        }

    # Step 3: Create draft job in DB
    job_id = str(uuid.uuid4())
    slug_base = (extracted.get("job_title") or "pdf-upload").lower()
    import re
    slug = re.sub(r"[^\w\s-]", "", slug_base)
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")[:100]
    slug = f"{slug}-{job_id[:8]}"

    with Session(sync_engine) as session:
        session.execute(
            text("""
                INSERT INTO job_vacancies (
                    id, job_title, slug, organization, department, job_type,
                    qualification_level, total_vacancies, description, short_description,
                    notification_date, application_start, application_end, exam_start,
                    fee_general, fee_obc, fee_sc_st, fee_ews, fee_female,
                    salary_initial, salary_max,
                    eligibility, selection_process, source_url,
                    source_pdf_path, status, source, created_by, created_at, updated_at,
                    vacancy_breakdown, application_details, documents, exam_details, salary
                ) VALUES (
                    :id, :job_title, :slug, :organization, :department, :job_type,
                    :qualification_level, :total_vacancies, :description, :short_description,
                    :notification_date, :application_start, :application_end, :exam_start,
                    :fee_general, :fee_obc, :fee_sc_st, :fee_ews, :fee_female,
                    :salary_initial, :salary_max,
                    CAST(:eligibility AS jsonb), CAST(:selection_process AS jsonb), :source_url,
                    :source_pdf_path, 'draft', 'pdf_upload', :created_by, NOW(), NOW(),
                    CAST('{}' AS jsonb), CAST('{}' AS jsonb), CAST('[]' AS jsonb), CAST('{}' AS jsonb), CAST('{}' AS jsonb)
                )
            """),
            {
                "id": job_id,
                "job_title": (extracted.get("job_title") or "Untitled")[:500],
                "slug": slug,
                "organization": (extracted.get("organization") or "Unknown")[:255],
                "department": (extracted.get("department") or None),
                "job_type": "latest_job",
                "qualification_level": extracted.get("qualification_level"),
                "total_vacancies": extracted.get("total_vacancies"),
                "description": extracted.get("description"),
                "short_description": extracted.get("short_description"),
                "notification_date": extracted.get("notification_date"),
                "application_start": extracted.get("application_start"),
                "application_end": extracted.get("application_end"),
                "exam_start": extracted.get("exam_start"),
                "fee_general": extracted.get("fee_general"),
                "fee_obc": extracted.get("fee_obc"),
                "fee_sc_st": extracted.get("fee_sc_st"),
                "fee_ews": extracted.get("fee_ews"),
                "fee_female": extracted.get("fee_female"),
                "salary_initial": extracted.get("salary_initial"),
                "salary_max": extracted.get("salary_max"),
                "eligibility": __import__("json").dumps(extracted.get("eligibility") or {}),
                "selection_process": __import__("json").dumps(extracted.get("selection_process") or []),
                "source_url": extracted.get("source_url"),
                "source_pdf_path": pdf_path,
                "created_by": admin_id,
            },
        )
        session.commit()

    logger.info(f"Created draft job {job_id} from PDF: {pdf_path}")

    # Delete the uploaded PDF unless PDF_KEEP_AFTER_EXTRACTION is True
    from app.config import settings
    if not settings.PDF_KEEP_AFTER_EXTRACTION:
        try:
            os.unlink(pdf_path)
        except OSError as e:
            logger.warning(f"Could not delete PDF file {pdf_path}: {e}")

    return {"status": "ok", "job_id": job_id, "extracted_fields": list(extracted.keys())}
