"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
async def health_check():
    """Service health check. Used by Docker healthcheck and monitoring."""
    return {"status": "ok", "service": "hermes-backend"}
