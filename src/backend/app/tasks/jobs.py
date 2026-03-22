"""Job-related Celery tasks.

Scheduled:
  close_expired_job_listings  — Daily 02:30 UTC

Event-driven:
  extract_job_from_pdf        — Process uploaded PDF → AI extraction → create draft job
"""

import logging
import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.celery_app import celery
from app.database import sync_engine

logger = logging.getLogger(__name__)


@celery.task(name="app.tasks.jobs.close_expired_job_listings")
def close_expired_job_listings():
    """Auto-close jobs past application_end. Daily 02:30 UTC."""
    with Session(sync_engine) as session:
        result = session.execute(
            text("""
                UPDATE job_vacancies
                SET status = 'cancelled', updated_at = NOW()
                WHERE status = 'active'
                  AND application_end IS NOT NULL
                  AND application_end < CURRENT_DATE
                RETURNING id
            """)
        )
        closed_ids = [str(row[0]) for row in result.fetchall()]
        session.commit()

    logger.info(f"Closed {len(closed_ids)} expired job listings")
    return {"closed_count": len(closed_ids)}


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
    return {"status": "ok", "job_id": job_id, "extracted_fields": list(extracted.keys())}
