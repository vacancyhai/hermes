"""Job document endpoints — admit cards, answer keys, results.

Public (read-only):
  GET  /api/v1/jobs/{job_id}/admit-cards   — list admit cards for a job
  GET  /api/v1/jobs/{job_id}/answer-keys   — list answer keys for a job
  GET  /api/v1/jobs/{job_id}/results       — list results for a job

Note: Admin CRUD operations have been moved to top-level endpoints:
  /api/v1/admin/admit-cards
  /api/v1/admin/answer-keys
  /api/v1/admin/results
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.admit_card import AdmitCard
from app.models.answer_key import AnswerKey
from app.models.result import Result
from app.models.job import Job
from app.schemas.jobs import (
    AdmitCardResponse,
    AnswerKeyResponse,
    ResultResponse,
)

public_router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


# ── helpers ────────────────────────────────────────────────────────────────────

async def _require_job(job_id: uuid.UUID, db: AsyncSession) -> Job:
    """Get job by ID (any status)."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC — read-only
# ══════════════════════════════════════════════════════════════════════════════


@public_router.get("/{job_id}/admit-cards", response_model=list[AdmitCardResponse])
async def list_admit_cards(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """List all admit cards for a job, ordered by phase."""
    await _require_job(job_id, db)
    rows = await db.execute(
        select(AdmitCard)
        .where(AdmitCard.job_id == job_id)
        .order_by(AdmitCard.phase_number.nulls_last(), AdmitCard.published_at.desc())
    )
    return [AdmitCardResponse.model_validate(r) for r in rows.scalars().all()]


@public_router.get("/{job_id}/answer-keys", response_model=list[AnswerKeyResponse])
async def list_answer_keys(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """List all answer keys for a job, ordered by phase."""
    await _require_job(job_id, db)
    rows = await db.execute(
        select(AnswerKey)
        .where(AnswerKey.job_id == job_id)
        .order_by(AnswerKey.phase_number.nulls_last(), AnswerKey.answer_key_type, AnswerKey.published_at.desc())
    )
    return [AnswerKeyResponse.model_validate(r) for r in rows.scalars().all()]


@public_router.get("/{job_id}/results", response_model=list[ResultResponse])
async def list_results(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """List all results for a job, ordered by phase."""
    await _require_job(job_id, db)
    rows = await db.execute(
        select(Result)
        .where(Result.job_id == job_id)
        .order_by(Result.phase_number.nulls_last(), Result.published_at.desc())
    )
    return [ResultResponse.model_validate(r) for r in rows.scalars().all()]
