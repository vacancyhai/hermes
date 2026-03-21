"""Admin endpoints.

GET    /api/v1/admin/stats               — Dashboard stats
GET    /api/v1/admin/analytics           — Platform analytics
GET    /api/v1/admin/jobs                — List all jobs
POST   /api/v1/admin/jobs                — Create job
PUT    /api/v1/admin/jobs/:id            — Update job
DELETE /api/v1/admin/jobs/:id            — Delete job
POST   /api/v1/admin/jobs/upload-pdf     — Upload PDF for AI extraction
GET    /api/v1/admin/jobs/:id/review     — Get draft with AI-extracted data
PUT    /api/v1/admin/jobs/:id/approve    — Approve draft → active
GET    /api/v1/admin/users               — List all users
GET    /api/v1/admin/users/:id           — User details
PUT    /api/v1/admin/users/:id/status    — Suspend/activate user
PUT    /api/v1/admin/users/:id/role      — Change user role
GET    /api/v1/admin/logs                — Admin activity logs
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# --- Dashboard ---

@router.get("/stats")
async def dashboard_stats():
    """Dashboard stats. TODO: Implement."""
    return {"message": "Not implemented"}


@router.get("/analytics")
async def analytics():
    """Platform analytics. TODO: Implement."""
    return {"message": "Not implemented"}


# --- Job management ---

@router.get("/jobs")
async def list_all_jobs():
    """List all jobs (admin view, supports ?status=draft filter).
    TODO: Implement.
    """
    return {"data": [], "pagination": {"limit": 20, "offset": 0, "total": 0, "has_more": False}}


@router.post("/jobs")
async def create_job():
    """Create a job (Admin only). TODO: Implement."""
    return {"message": "Not implemented"}


@router.post("/jobs/upload-pdf")
async def upload_pdf():
    """Upload notification PDF → trigger AI extraction. TODO: Implement."""
    return {"message": "Not implemented"}


@router.get("/jobs/{job_id}/review")
async def review_draft(job_id: str):
    """Get draft job with AI-extracted data for review. TODO: Implement."""
    return {"message": "Not implemented"}


@router.put("/jobs/{job_id}/approve")
async def approve_draft(job_id: str):
    """Approve draft → status='active', triggers notifications. TODO: Implement."""
    return {"message": "Not implemented"}


@router.put("/jobs/{job_id}")
async def update_job(job_id: str):
    """Update a job. TODO: Implement."""
    return {"message": "Not implemented"}


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job. TODO: Implement."""
    return {"message": "Not implemented"}


# --- User management ---

@router.get("/users")
async def list_users():
    """List all users. TODO: Implement."""
    return {"data": [], "pagination": {"limit": 20, "offset": 0, "total": 0, "has_more": False}}


@router.get("/users/{user_id}")
async def get_user(user_id: str):
    """Get user details. TODO: Implement."""
    return {"message": "Not implemented"}


@router.put("/users/{user_id}/status")
async def update_user_status(user_id: str):
    """Suspend/activate user. TODO: Implement."""
    return {"message": "Not implemented"}


@router.put("/users/{user_id}/role")
async def update_user_role(user_id: str):
    """Change user role. TODO: Implement."""
    return {"message": "Not implemented"}


# --- Logs ---

@router.get("/logs")
async def admin_logs():
    """Admin activity logs. TODO: Implement."""
    return {"data": [], "pagination": {"limit": 20, "offset": 0, "total": 0, "has_more": False}}
