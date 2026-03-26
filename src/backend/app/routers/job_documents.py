"""Job document endpoints — admit cards, answer keys, results.

Public (read-only, active jobs only):
  GET  /api/v1/jobs/{job_id}/admit-cards   — list admit cards for a job
  GET  /api/v1/jobs/{job_id}/answer-keys   — list answer keys for a job
  GET  /api/v1/jobs/{job_id}/results       — list results for a job

Admin CRUD (operator+):
  POST   /api/v1/admin/jobs/{job_id}/admit-cards            — add admit card
  PUT    /api/v1/admin/jobs/{job_id}/admit-cards/{doc_id}   — update admit card
  DELETE /api/v1/admin/jobs/{job_id}/admit-cards/{doc_id}   — delete admit card

  POST   /api/v1/admin/jobs/{job_id}/answer-keys            — add answer key
  PUT    /api/v1/admin/jobs/{job_id}/answer-keys/{doc_id}   — update answer key
  DELETE /api/v1/admin/jobs/{job_id}/answer-keys/{doc_id}   — delete answer key

  POST   /api/v1/admin/jobs/{job_id}/results                — add result
  PUT    /api/v1/admin/jobs/{job_id}/results/{doc_id}        — update result
  DELETE /api/v1/admin/jobs/{job_id}/results/{doc_id}        — delete result
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_operator
from app.models.job_admit_card import JobAdmitCard
from app.models.job_answer_key import JobAnswerKey
from app.models.job_result import JobResult
from app.models.job_vacancy import JobVacancy
from app.schemas.jobs import (
    AdmitCardCreateRequest, AdmitCardUpdateRequest, AdmitCardResponse,
    AnswerKeyCreateRequest, AnswerKeyUpdateRequest, AnswerKeyResponse,
    ResultCreateRequest, ResultUpdateRequest, ResultResponse,
)

public_router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])
admin_router = APIRouter(prefix="/api/v1/admin/jobs", tags=["admin"])


# ── helpers ────────────────────────────────────────────────────────────────────

async def _require_job(job_id: uuid.UUID, db: AsyncSession) -> JobVacancy:
    result = await db.execute(select(JobVacancy).where(JobVacancy.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


async def _require_active_job(job_id: uuid.UUID, db: AsyncSession) -> JobVacancy:
    """Get job by ID (any status). Note: Function name kept for backward compatibility."""
    result = await db.execute(
        select(JobVacancy).where(JobVacancy.id == job_id)
    )
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
    await _require_active_job(job_id, db)
    rows = await db.execute(
        select(JobAdmitCard)
        .where(JobAdmitCard.job_id == job_id)
        .order_by(JobAdmitCard.phase_number.nulls_last(), JobAdmitCard.published_at.desc())
    )
    return [AdmitCardResponse.model_validate(r) for r in rows.scalars().all()]


@public_router.get("/{job_id}/answer-keys", response_model=list[AnswerKeyResponse])
async def list_answer_keys(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """List all answer keys for a job, ordered by phase."""
    await _require_active_job(job_id, db)
    rows = await db.execute(
        select(JobAnswerKey)
        .where(JobAnswerKey.job_id == job_id)
        .order_by(JobAnswerKey.phase_number.nulls_last(), JobAnswerKey.answer_key_type, JobAnswerKey.published_at.desc())
    )
    return [AnswerKeyResponse.model_validate(r) for r in rows.scalars().all()]


@public_router.get("/{job_id}/results", response_model=list[ResultResponse])
async def list_results(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """List all results for a job, ordered by phase."""
    await _require_active_job(job_id, db)
    rows = await db.execute(
        select(JobResult)
        .where(JobResult.job_id == job_id)
        .order_by(JobResult.phase_number.nulls_last(), JobResult.published_at.desc())
    )
    return [ResultResponse.model_validate(r) for r in rows.scalars().all()]


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — admit cards
# ══════════════════════════════════════════════════════════════════════════════


@admin_router.post("/{job_id}/admit-cards", status_code=status.HTTP_201_CREATED, response_model=AdmitCardResponse)
async def create_admit_card(
    job_id: uuid.UUID,
    body: AdmitCardCreateRequest,
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Add an admit card to a job."""
    await _require_job(job_id, db)
    doc = JobAdmitCard(
        job_id=job_id,
        phase_number=body.phase_number,
        title=body.title,
        download_url=body.download_url,
        valid_from=body.valid_from,
        valid_until=body.valid_until,
        notes=body.notes,
        published_at=body.published_at,
    )
    db.add(doc)
    await db.flush()
    return AdmitCardResponse.model_validate(doc)


@admin_router.put("/{job_id}/admit-cards/{doc_id}", response_model=AdmitCardResponse)
async def update_admit_card(
    job_id: uuid.UUID,
    doc_id: uuid.UUID,
    body: AdmitCardUpdateRequest,
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Update an admit card."""
    result = await db.execute(
        select(JobAdmitCard).where(JobAdmitCard.id == doc_id, JobAdmitCard.job_id == job_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admit card not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)

    await db.flush()
    return AdmitCardResponse.model_validate(doc)


@admin_router.delete("/{job_id}/admit-cards/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admit_card(
    job_id: uuid.UUID,
    doc_id: uuid.UUID,
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Delete an admit card."""
    result = await db.execute(
        select(JobAdmitCard).where(JobAdmitCard.id == doc_id, JobAdmitCard.job_id == job_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admit card not found")
    await db.delete(doc)


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — answer keys
# ══════════════════════════════════════════════════════════════════════════════


@admin_router.post("/{job_id}/answer-keys", status_code=status.HTTP_201_CREATED, response_model=AnswerKeyResponse)
async def create_answer_key(
    job_id: uuid.UUID,
    body: AnswerKeyCreateRequest,
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Add an answer key to a job."""
    await _require_job(job_id, db)
    doc = JobAnswerKey(
        job_id=job_id,
        phase_number=body.phase_number,
        title=body.title,
        answer_key_type=body.answer_key_type,
        files=body.files,
        objection_url=body.objection_url,
        objection_deadline=body.objection_deadline,
        published_at=body.published_at,
    )
    db.add(doc)
    await db.flush()
    return AnswerKeyResponse.model_validate(doc)


@admin_router.put("/{job_id}/answer-keys/{doc_id}", response_model=AnswerKeyResponse)
async def update_answer_key(
    job_id: uuid.UUID,
    doc_id: uuid.UUID,
    body: AnswerKeyUpdateRequest,
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Update an answer key."""
    result = await db.execute(
        select(JobAnswerKey).where(JobAnswerKey.id == doc_id, JobAnswerKey.job_id == job_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer key not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)

    await db.flush()
    return AnswerKeyResponse.model_validate(doc)


@admin_router.delete("/{job_id}/answer-keys/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_answer_key(
    job_id: uuid.UUID,
    doc_id: uuid.UUID,
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Delete an answer key."""
    result = await db.execute(
        select(JobAnswerKey).where(JobAnswerKey.id == doc_id, JobAnswerKey.job_id == job_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer key not found")
    await db.delete(doc)


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — results
# ══════════════════════════════════════════════════════════════════════════════


@admin_router.post("/{job_id}/results", status_code=status.HTTP_201_CREATED, response_model=ResultResponse)
async def create_result(
    job_id: uuid.UUID,
    body: ResultCreateRequest,
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Add a result to a job."""
    await _require_job(job_id, db)
    doc = JobResult(
        job_id=job_id,
        phase_number=body.phase_number,
        title=body.title,
        result_type=body.result_type,
        download_url=body.download_url,
        cutoff_marks=body.cutoff_marks,
        total_qualified=body.total_qualified,
        notes=body.notes,
        published_at=body.published_at,
    )
    db.add(doc)
    await db.flush()
    return ResultResponse.model_validate(doc)


@admin_router.put("/{job_id}/results/{doc_id}", response_model=ResultResponse)
async def update_result(
    job_id: uuid.UUID,
    doc_id: uuid.UUID,
    body: ResultUpdateRequest,
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Update a result."""
    result = await db.execute(
        select(JobResult).where(JobResult.id == doc_id, JobResult.job_id == job_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)

    await db.flush()
    return ResultResponse.model_validate(doc)


@admin_router.delete("/{job_id}/results/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_result(
    job_id: uuid.UUID,
    doc_id: uuid.UUID,
    admin=Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    """Delete a result."""
    result = await db.execute(
        select(JobResult).where(JobResult.id == doc_id, JobResult.job_id == job_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found")
    await db.delete(doc)
