"""Watch (track) endpoints — watch jobs and entrance exams for deadline notifications.

POST   /api/v1/jobs/{job_id}/watch            — Watch a job
DELETE /api/v1/jobs/{job_id}/watch            — Unwatch a job
POST   /api/v1/entrance-exams/{exam_id}/watch — Watch an entrance exam
DELETE /api/v1/entrance-exams/{exam_id}/watch — Unwatch an entrance exam
GET    /api/v1/users/me/watched               — List all watched jobs + exams
"""

import uuid
from typing import Annotated, Any

from app.dependencies import get_current_user, get_db
from app.models.entrance_exam import EntranceExam
from app.models.job import Job
from app.models.user_watch import UserWatch
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["watches"])

MAX_WATCHES = 100


# ── helpers ────────────────────────────────────────────────────────────────────


async def _get_watch(
    user_id: uuid.UUID, entity_type: str, entity_id: uuid.UUID, db: AsyncSession
):
    result = await db.execute(
        select(UserWatch).where(
            UserWatch.user_id == user_id,
            UserWatch.entity_type == entity_type,
            UserWatch.entity_id == entity_id,
        )
    )
    return result.scalar_one_or_none()


async def _count_watches(user_id: uuid.UUID, db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(UserWatch).where(UserWatch.user_id == user_id)
    )
    return result.scalar()


# ══════════════════════════════════════════════════════════════════════════════
# Job Watch
# ══════════════════════════════════════════════════════════════════════════════


@router.post("/api/v1/jobs/{job_id}/watch", status_code=status.HTTP_200_OK)
async def watch_job(
    job_id: uuid.UUID,
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Watch a job to receive deadline reminders and update notifications. Idempotent."""
    user, _ = current_user

    result = await db.execute(select(Job).where(Job.id == job_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    if await _get_watch(user.id, "job", job_id, db):
        return {"message": "Already watching this job", "watching": True}

    if await _count_watches(user.id, db) >= MAX_WATCHES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_WATCHES} watched items allowed",
        )

    db.add(UserWatch(user_id=user.id, entity_type="job", entity_id=job_id))
    await db.commit()
    return {"message": "Now watching this job", "watching": True}


@router.delete("/api/v1/jobs/{job_id}/watch", status_code=status.HTTP_200_OK)
async def unwatch_job(
    job_id: uuid.UUID,
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Stop watching a job."""
    user, _ = current_user

    watch = await _get_watch(user.id, "job", job_id, db)
    if not watch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not watching this job"
        )

    await db.delete(watch)
    await db.commit()
    return {"message": "Unwatched job", "watching": False}


# ══════════════════════════════════════════════════════════════════════════════
# Entrance Exam Watch
# ══════════════════════════════════════════════════════════════════════════════


@router.post("/api/v1/entrance-exams/{exam_id}/watch", status_code=status.HTTP_200_OK)
async def watch_exam(
    exam_id: uuid.UUID,
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Watch an entrance exam to receive deadline reminders and update notifications. Idempotent."""
    user, _ = current_user

    result = await db.execute(select(EntranceExam).where(EntranceExam.id == exam_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Entrance exam not found"
        )

    if await _get_watch(user.id, "exam", exam_id, db):
        return {"message": "Already watching this exam", "watching": True}

    if await _count_watches(user.id, db) >= MAX_WATCHES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_WATCHES} watched items allowed",
        )

    db.add(UserWatch(user_id=user.id, entity_type="exam", entity_id=exam_id))
    await db.commit()
    return {"message": "Now watching this exam", "watching": True}


@router.delete("/api/v1/entrance-exams/{exam_id}/watch", status_code=status.HTTP_200_OK)
async def unwatch_exam(
    exam_id: uuid.UUID,
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Stop watching an entrance exam."""
    user, _ = current_user

    watch = await _get_watch(user.id, "exam", exam_id, db)
    if not watch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not watching this exam"
        )

    await db.delete(watch)
    await db.commit()
    return {"message": "Unwatched exam", "watching": False}


# ══════════════════════════════════════════════════════════════════════════════
# List Watched
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/api/v1/users/me/watched")
async def list_watched(
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all watched jobs and entrance exams for the current user."""
    user, _ = current_user

    watches_result = await db.execute(
        select(UserWatch)
        .where(UserWatch.user_id == user.id)
        .order_by(UserWatch.created_at.desc())
    )
    watches = watches_result.scalars().all()

    job_ids = [w.entity_id for w in watches if w.entity_type == "job"]
    exam_ids = [w.entity_id for w in watches if w.entity_type == "exam"]

    # Fetch into lookup dicts to allow re-ordering by watch.created_at
    jobs_by_id: dict = {}
    if job_ids:
        result = await db.execute(select(Job).where(Job.id.in_(job_ids)))
        jobs_by_id = {
            j.id: {
                "id": str(j.id),
                "job_title": j.job_title,
                "slug": j.slug,
                "organization": j.organization,
                "application_end": (
                    str(j.application_end) if j.application_end else None
                ),
                "status": j.status,
            }
            for j in result.scalars().all()
        }

    exams_by_id: dict = {}
    if exam_ids:
        result = await db.execute(
            select(EntranceExam).where(EntranceExam.id.in_(exam_ids))
        )
        exams_by_id = {
            e.id: {
                "id": str(e.id),
                "exam_name": e.exam_name,
                "slug": e.slug,
                "conducting_body": e.conducting_body,
                "application_end": (
                    str(e.application_end) if e.application_end else None
                ),
                "status": e.status,
            }
            for e in result.scalars().all()
        }

    # Re-assemble in watch created_at order (watches already sorted desc)
    jobs = [
        jobs_by_id[w.entity_id]
        for w in watches
        if w.entity_type == "job" and w.entity_id in jobs_by_id
    ]
    exams = [
        exams_by_id[w.entity_id]
        for w in watches
        if w.entity_type == "exam" and w.entity_id in exams_by_id
    ]

    return {"jobs": jobs, "exams": exams, "total": len(jobs) + len(exams)}
