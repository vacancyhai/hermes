"""Organization endpoints.

Public:
  GET    /api/v1/organizations               — List all organizations (with job count)
  GET    /api/v1/organizations/{slug}        — Get organization detail + recent jobs

Authenticated (user):
  POST   /api/v1/organizations/{org_id}/track   — Follow an organization
  DELETE /api/v1/organizations/{org_id}/track   — Unfollow an organization
  GET    /api/v1/organizations/{org_id}/track   — Check follow status
"""

import uuid
from typing import Annotated, Any

from app.dependencies import get_current_user, get_db
from app.models.admission import Admission
from app.models.job import Job
from app.models.organization import Organization
from app.models.user_track import UserTrack
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["organizations"])

MAX_TRACKS = 100


# ── helpers ─────────────────────────────────────────────────────────────────────


async def _get_org_or_404(org_id: uuid.UUID, db: AsyncSession) -> Organization:
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )
    return org


async def _get_track(user_id: uuid.UUID, entity_id: uuid.UUID, db: AsyncSession):
    result = await db.execute(
        select(UserTrack).where(
            UserTrack.user_id == user_id,
            UserTrack.entity_type == "organization",
            UserTrack.entity_id == entity_id,
        )
    )
    return result.scalar_one_or_none()


async def _count_tracks(user_id: uuid.UUID, db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(UserTrack).where(UserTrack.user_id == user_id)
    )
    return result.scalar()


def _org_to_dict(
    org: Organization, job_count: int = 0, admission_count: int = 0
) -> dict:
    return {
        "id": str(org.id),
        "name": org.name,
        "slug": org.slug,
        "org_type": org.org_type,
        "short_name": org.short_name,
        "logo_url": org.logo_url,
        "website_url": org.website_url,
        "job_count": job_count,
        "admission_count": admission_count,
        "created_at": org.created_at.isoformat() if org.created_at else None,
    }


# ── Public endpoints ─────────────────────────────────────────────────────────────


@router.get("/api/v1/organizations")
async def list_organizations(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: Annotated[str | None, Query(max_length=255)] = None,
    org_type: Annotated[str | None, Query(max_length=20)] = None,
):
    """List all organizations with active job/admission counts.

    Filter by org_type ('jobs', 'admissions', 'both') — passing 'jobs' returns
    orgs with org_type IN ('jobs','both') and 'admissions' returns ('admissions','both').
    """
    query = select(Organization).order_by(Organization.name)
    count_query = select(func.count(Organization.id))

    if search:
        pattern = f"%{search}%"
        query = query.where(Organization.name.ilike(pattern))
        count_query = count_query.where(Organization.name.ilike(pattern))

    if org_type == "jobs":
        query = query.where(Organization.org_type.in_(["jobs", "both"]))
        count_query = count_query.where(Organization.org_type.in_(["jobs", "both"]))
    elif org_type == "admissions":
        query = query.where(Organization.org_type.in_(["admissions", "both"]))
        count_query = count_query.where(
            Organization.org_type.in_(["admissions", "both"])
        )

    total = (await db.execute(count_query)).scalar()
    orgs = (await db.execute(query.offset(offset).limit(limit))).scalars().all()

    org_ids = [o.id for o in orgs]
    job_counts: dict = {}
    admission_counts: dict = {}
    if org_ids:
        job_rows = (
            await db.execute(
                select(Job.organization_id, func.count(Job.id))
                .where(Job.organization_id.in_(org_ids))
                .group_by(Job.organization_id)
            )
        ).all()
        job_counts = {row[0]: row[1] for row in job_rows}
        adm_rows = (
            await db.execute(
                select(Admission.organization_id, func.count(Admission.id))
                .where(Admission.organization_id.in_(org_ids))
                .group_by(Admission.organization_id)
            )
        ).all()
        admission_counts = {row[0]: row[1] for row in adm_rows}

    return {
        "data": [
            _org_to_dict(o, job_counts.get(o.id, 0), admission_counts.get(o.id, 0))
            for o in orgs
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/api/v1/organizations/tracked")
async def list_tracked_organizations(
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all organizations followed by the current user."""
    user, _ = current_user
    rows = (
        (
            await db.execute(
                select(UserTrack).where(
                    UserTrack.user_id == user.id,
                    UserTrack.entity_type == "organization",
                )
            )
        )
        .scalars()
        .all()
    )
    org_ids = [r.entity_id for r in rows]
    if not org_ids:
        return {"data": []}
    orgs = (
        (await db.execute(select(Organization).where(Organization.id.in_(org_ids))))
        .scalars()
        .all()
    )
    return {"data": [_org_to_dict(o) for o in orgs]}


@router.get("/api/v1/organizations/{org_id}")
async def get_organization(
    org_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get organization detail and its recent active jobs."""
    org = await _get_org_or_404(org_id, db)

    jobs_result = await db.execute(
        select(Job)
        .where(Job.organization_id == org.id)
        .order_by(Job.created_at.desc())
        .limit(20)
    )
    jobs = [
        {
            "id": str(j.id),
            "job_title": j.job_title,
            "slug": j.slug,
            "status": j.status,
            "application_end": str(j.application_end) if j.application_end else None,
            "total_vacancies": j.total_vacancies,
        }
        for j in jobs_result.scalars().all()
    ]

    job_count = (
        await db.execute(
            select(func.count(Job.id)).where(Job.organization_id == org.id)
        )
    ).scalar()

    return {**_org_to_dict(org, job_count), "jobs": jobs}


# ── Authenticated track endpoints ────────────────────────────────────────────────


@router.post("/api/v1/organizations/{org_id}/track", status_code=status.HTTP_200_OK)
async def follow_organization(
    org_id: uuid.UUID,
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Follow an organization to receive notifications for all its new jobs. Idempotent."""
    user, _ = current_user
    await _get_org_or_404(org_id, db)

    if await _get_track(user.id, org_id, db):
        return {"message": "Already following this organization", "tracking": True}

    if await _count_tracks(user.id, db) >= MAX_TRACKS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_TRACKS} tracked items allowed",
        )

    db.add(UserTrack(user_id=user.id, entity_type="organization", entity_id=org_id))
    return {"message": "Now following this organization", "tracking": True}


@router.delete("/api/v1/organizations/{org_id}/track", status_code=status.HTTP_200_OK)
async def unfollow_organization(
    org_id: uuid.UUID,
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Unfollow an organization."""
    user, _ = current_user

    track = await _get_track(user.id, org_id, db)
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not following this organization",
        )

    await db.delete(track)
    return {"message": "Unfollowed organization", "tracking": False}


@router.get("/api/v1/organizations/{org_id}/track", status_code=status.HTTP_200_OK)
async def organization_follow_status(
    org_id: uuid.UUID,
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Check whether the current user is following a specific organization."""
    user, _ = current_user
    tracking = await _get_track(user.id, org_id, db) is not None
    return {"tracking": tracking}
