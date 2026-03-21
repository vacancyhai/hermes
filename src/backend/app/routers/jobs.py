"""Job vacancy endpoints.

GET    /api/v1/jobs              — List (filterable, paginated)
GET    /api/v1/jobs/:slug        — Detail
GET    /api/v1/jobs/recommended  — Personalized matches
POST   /api/v1/jobs              — Create (Admin)
PUT    /api/v1/jobs/:id          — Update (Admin/Operator)
DELETE /api/v1/jobs/:id          — Soft delete (Admin)
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("")
async def list_jobs():
    """List jobs with filters: job_type, qualification_level, organization,
    department, status, is_featured, is_urgent, q (full-text search).
    Supports ?limit=N&offset=M pagination.
    TODO: Implement.
    """
    return {"data": [], "pagination": {"limit": 20, "offset": 0, "total": 0, "has_more": False}}


@router.get("/recommended")
async def recommended_jobs():
    """Personalized job matches based on user profile. TODO: Implement."""
    return {"data": [], "pagination": {"limit": 20, "offset": 0, "total": 0, "has_more": False}}


@router.get("/{slug}")
async def get_job(slug: str):
    """Job detail by slug. TODO: Implement."""
    return {"message": "Not implemented"}


@router.post("")
async def create_job():
    """Create a job vacancy (Admin only). TODO: Implement."""
    return {"message": "Not implemented"}


@router.put("/{job_id}")
async def update_job(job_id: str):
    """Update a job vacancy (Admin/Operator). TODO: Implement."""
    return {"message": "Not implemented"}


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    """Soft delete a job vacancy (Admin only). TODO: Implement."""
    return {"message": "Not implemented"}
