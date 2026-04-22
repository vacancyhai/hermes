"""Celery tasks — pre-compute and store eligibility for jobs and admissions.

Tasks:
  recompute_eligibility_for_user(user_id)
      Called when a user updates their profile.
      Runs check_job_eligibility + check_admission_eligibility against every
      active job/admission and upserts results into user_job_eligibility and
      user_admission_eligibility tables.

  recompute_eligibility_for_job(job_id)
      Called when a job is created or updated.
      Runs check_job_eligibility for every user that has a profile and upserts
      results into user_job_eligibility.

  recompute_eligibility_for_admission(admission_id)
      Called when an admission is created or updated.
      Runs check_admission_eligibility for every user that has a profile and
      upserts results into user_admission_eligibility.
"""

import logging
from datetime import datetime, timezone

from app.celery_app import celery
from app.database import sync_engine
from app.models.admission import Admission
from app.models.job import Job
from app.models.user_eligibility import UserAdmissionEligibility, UserJobEligibility
from app.models.user_profile import UserProfile
from app.services.matching import check_admission_eligibility, check_job_eligibility
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_ACTIVE_STATUSES = ("active", "upcoming")


def _upsert_job_rows(session: Session, rows: list[dict]) -> None:
    if not rows:
        return
    stmt = insert(UserJobEligibility).values(rows)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_job_elig_user_job",
        set_={
            "status": stmt.excluded.status,
            "reasons": stmt.excluded.reasons,
            "computed_at": stmt.excluded.computed_at,
        },
    )
    session.execute(stmt)


def _upsert_admission_rows(session: Session, rows: list[dict]) -> None:
    if not rows:
        return
    stmt = insert(UserAdmissionEligibility).values(rows)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_adm_elig_user_admission",
        set_={
            "status": stmt.excluded.status,
            "reasons": stmt.excluded.reasons,
            "computed_at": stmt.excluded.computed_at,
        },
    )
    session.execute(stmt)


@celery.task(name="app.tasks.eligibility.recompute_eligibility_for_user")
def recompute_eligibility_for_user(user_id: str) -> dict:
    """Recompute all job + admission eligibility for one user after profile update."""
    now = datetime.now(timezone.utc)
    with Session(sync_engine) as session:
        profile = session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        ).scalar_one_or_none()
        if not profile:
            return {"skipped": True, "reason": "profile not found"}

        jobs = (
            session.execute(select(Job).where(Job.status.in_(_ACTIVE_STATUSES)))
            .scalars()
            .all()
        )

        admissions = (
            session.execute(
                select(Admission).where(Admission.status.in_(_ACTIVE_STATUSES))
            )
            .scalars()
            .all()
        )

        job_rows = []
        for job in jobs:
            result = check_job_eligibility(job, profile)
            job_rows.append(
                {
                    "user_id": user_id,
                    "job_id": str(job.id),
                    "status": result["status"],
                    "reasons": result["reasons"],
                    "computed_at": now,
                }
            )

        adm_rows = []
        for adm in admissions:
            result = check_admission_eligibility(adm, profile)
            adm_rows.append(
                {
                    "user_id": user_id,
                    "admission_id": str(adm.id),
                    "status": result["status"],
                    "reasons": result["reasons"],
                    "computed_at": now,
                }
            )

        _upsert_job_rows(session, job_rows)
        _upsert_admission_rows(session, adm_rows)
        session.commit()

    logger.info(
        "eligibility_recomputed_for_user",
        extra={"user_id": user_id, "jobs": len(job_rows), "admissions": len(adm_rows)},
    )
    return {"user_id": user_id, "jobs": len(job_rows), "admissions": len(adm_rows)}


@celery.task(name="app.tasks.eligibility.recompute_eligibility_for_job")
def recompute_eligibility_for_job(job_id: str) -> dict:
    """Recompute eligibility for all users against one job after job create/update.

    If the job status is no longer active/upcoming, all rows for this job are
    deleted from job_eligibility instead of recomputed.
    """
    now = datetime.now(timezone.utc)
    with Session(sync_engine) as session:
        job = session.get(Job, job_id)
        if not job:
            return {"skipped": True, "reason": "job not found"}

        if job.status not in _ACTIVE_STATUSES:
            deleted = session.execute(
                delete(UserJobEligibility).where(UserJobEligibility.job_id == job_id)
            ).rowcount
            session.commit()
            logger.info(
                "eligibility_purged_for_job",
                extra={"job_id": job_id, "status": job.status, "deleted": deleted},
            )
            return {"job_id": job_id, "purged": deleted}

        profiles = session.execute(select(UserProfile)).scalars().all()

        rows = []
        for profile in profiles:
            result = check_job_eligibility(job, profile)
            rows.append(
                {
                    "user_id": str(profile.user_id),
                    "job_id": job_id,
                    "status": result["status"],
                    "reasons": result["reasons"],
                    "computed_at": now,
                }
            )

        _upsert_job_rows(session, rows)
        session.commit()

    logger.info(
        "eligibility_recomputed_for_job",
        extra={"job_id": job_id, "users": len(rows)},
    )
    return {"job_id": job_id, "users": len(rows)}


@celery.task(name="app.tasks.eligibility.recompute_eligibility_for_admission")
def recompute_eligibility_for_admission(admission_id: str) -> dict:
    """Recompute eligibility for all users against one admission after create/update.

    If the admission status is no longer active/upcoming, all rows for this
    admission are deleted from admission_eligibility instead of recomputed.
    """
    now = datetime.now(timezone.utc)
    with Session(sync_engine) as session:
        admission = session.get(Admission, admission_id)
        if not admission:
            return {"skipped": True, "reason": "admission not found"}

        if admission.status not in _ACTIVE_STATUSES:
            deleted = session.execute(
                delete(UserAdmissionEligibility).where(
                    UserAdmissionEligibility.admission_id == admission_id
                )
            ).rowcount
            session.commit()
            logger.info(
                "eligibility_purged_for_admission",
                extra={
                    "admission_id": admission_id,
                    "status": admission.status,
                    "deleted": deleted,
                },
            )
            return {"admission_id": admission_id, "purged": deleted}

        profiles = session.execute(select(UserProfile)).scalars().all()

        rows = []
        for profile in profiles:
            result = check_admission_eligibility(admission, profile)
            rows.append(
                {
                    "user_id": str(profile.user_id),
                    "admission_id": admission_id,
                    "status": result["status"],
                    "reasons": result["reasons"],
                    "computed_at": now,
                }
            )

        _upsert_admission_rows(session, rows)
        session.commit()

    logger.info(
        "eligibility_recomputed_for_admission",
        extra={"admission_id": admission_id, "users": len(rows)},
    )
    return {"admission_id": admission_id, "users": len(rows)}
