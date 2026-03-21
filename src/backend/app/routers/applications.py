"""Application tracking endpoints.

GET    /api/v1/applications       — List own applications
POST   /api/v1/applications       — Track a job
DELETE /api/v1/applications/:id   — Remove from tracker
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/applications", tags=["applications"])


@router.get("")
async def list_applications():
    """List own tracked applications. TODO: Implement."""
    return {"data": [], "pagination": {"limit": 20, "offset": 0, "total": 0, "has_more": False}}


@router.post("")
async def track_job():
    """Track / save a job application. TODO: Implement."""
    return {"message": "Not implemented"}


@router.delete("/{application_id}")
async def remove_application(application_id: str):
    """Remove a job from tracker. TODO: Implement."""
    return {"message": "Not implemented"}
