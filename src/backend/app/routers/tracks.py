"""Track endpoints — track jobs and admissions for deadline notifications.

POST   /api/v1/jobs/{job_id}/track               — Track a job
DELETE /api/v1/jobs/{job_id}/track               — Untrack a job
POST   /api/v1/admissions/{admission_id}/track   — Track an admission
DELETE /api/v1/admissions/{admission_id}/track   — Untrack an admission
GET    /api/v1/users/me/tracked                  — List all tracked jobs + admissions
"""

import uuid
from typing import Annotated, Any

from app.dependencies import get_current_user, get_db
from app.models.admission import Admission
from app.models.job import Job
from app.models.user_track import UserTrack
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["tracks"])

MAX_TRACKS = 100


# ── helpers ────────────────────────────────────────────────────────────────────


async def _get_track(
    user_id: uuid.UUID, entity_type: str, entity_id: uuid.UUID, db: AsyncSession
):
    result = await db.execute(
        select(UserTrack).where(
            UserTrack.user_id == user_id,
            UserTrack.entity_type == entity_type,
            UserTrack.entity_id == entity_id,
        )
    )
    return result.scalar_one_or_none()


async def _count_tracks(user_id: uuid.UUID, db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(UserTrack).where(UserTrack.user_id == user_id)
    )
    return result.scalar()


# Job Track


@router.post("/api/v1/jobs/{job_id}/track", status_code=status.HTTP_200_OK)
async def track_job(
    job_id: uuid.UUID,
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Track a job to receive deadline reminders and update notifications. Idempotent."""
    user, _ = current_user

    result = await db.execute(select(Job).where(Job.id == job_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    if await _get_track(user.id, "job", job_id, db):
        return {"message": "Already tracking this job", "tracking": True}

    if await _count_tracks(user.id, db) >= MAX_TRACKS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_TRACKS} tracked items allowed",
        )

    db.add(UserTrack(user_id=user.id, entity_type="job", entity_id=job_id))
    return {"message": "Now tracking this job", "tracking": True}


@router.delete("/api/v1/jobs/{job_id}/track", status_code=status.HTTP_200_OK)
async def untrack_job(
    job_id: uuid.UUID,
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Stop tracking a job."""
    user, _ = current_user

    track = await _get_track(user.id, "job", job_id, db)
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not tracking this job"
        )

    await db.delete(track)
    return {"message": "Untracked job", "tracking": False}


@router.get("/api/v1/jobs/{job_id}/track", status_code=status.HTTP_200_OK)
async def job_track_status(
    job_id: uuid.UUID,
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Check whether the current user is tracking a specific job."""
    user, _ = current_user
    tracking = await _get_track(user.id, "job", job_id, db) is not None
    return {"tracking": tracking}


# Admission Track


@router.post("/api/v1/admissions/{admission_id}/track", status_code=status.HTTP_200_OK)
async def track_admission(
    admission_id: uuid.UUID,
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Track an admission to receive deadline reminders and update notifications. Idempotent."""
    user, _ = current_user

    result = await db.execute(select(Admission).where(Admission.id == admission_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Admission not found"
        )

    if await _get_track(user.id, "admission", admission_id, db):
        return {"message": "Already tracking this admission", "tracking": True}

    if await _count_tracks(user.id, db) >= MAX_TRACKS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_TRACKS} tracked items allowed",
        )

    db.add(UserTrack(user_id=user.id, entity_type="admission", entity_id=admission_id))
    return {"message": "Now tracking this admission", "tracking": True}


@router.delete(
    "/api/v1/admissions/{admission_id}/track", status_code=status.HTTP_200_OK
)
async def untrack_admission(
    admission_id: uuid.UUID,
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Stop tracking an admission."""
    user, _ = current_user

    track = await _get_track(user.id, "admission", admission_id, db)
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not tracking this admission"
        )

    await db.delete(track)
    return {"message": "Untracked admission", "tracking": False}


@router.get("/api/v1/admissions/{admission_id}/track", status_code=status.HTTP_200_OK)
async def admission_track_status(
    admission_id: uuid.UUID,
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Check whether the current user is tracking a specific admission."""
    user, _ = current_user
    tracking = await _get_track(user.id, "admission", admission_id, db) is not None
    return {"tracking": tracking}


# List Tracked


@router.get("/api/v1/users/me/tracked")
async def list_tracked(
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all tracked jobs and admissions for the current user."""
    user, _ = current_user

    tracks_result = await db.execute(
        select(UserTrack)
        .where(UserTrack.user_id == user.id)
        .order_by(UserTrack.created_at.desc())
    )
    tracks = tracks_result.scalars().all()

    job_ids = [t.entity_id for t in tracks if t.entity_type == "job"]
    admission_ids = [t.entity_id for t in tracks if t.entity_type == "admission"]

    # Fetch into lookup dicts to allow re-ordering by track.created_at
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

    admissions_by_id: dict = {}
    if admission_ids:
        result = await db.execute(
            select(Admission).where(Admission.id.in_(admission_ids))
        )
        admissions_by_id = {
            e.id: {
                "id": str(e.id),
                "admission_name": e.admission_name,
                "slug": e.slug,
                "conducting_body": e.conducting_body,
                "application_end": (
                    str(e.application_end) if e.application_end else None
                ),
                "status": e.status,
            }
            for e in result.scalars().all()
        }

    # Re-assemble in track created_at order (tracks already sorted desc)
    jobs = [
        jobs_by_id[t.entity_id]
        for t in tracks
        if t.entity_type == "job" and t.entity_id in jobs_by_id
    ]
    admissions = [
        admissions_by_id[t.entity_id]
        for t in tracks
        if t.entity_type == "admission" and t.entity_id in admissions_by_id
    ]

    return {
        "jobs": jobs,
        "admissions": admissions,
        "total": len(jobs) + len(admissions),
    }
