"""Authentication endpoints.

POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/refresh
POST /api/v1/auth/forgot-password
POST /api/v1/auth/reset-password
GET  /api/v1/auth/verify-email/:token
GET  /api/v1/auth/csrf-token
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register")
async def register():
    """User registration. TODO: Implement."""
    return {"message": "Not implemented"}


@router.post("/login")
async def login():
    """User login → returns JWT access + refresh tokens. TODO: Implement."""
    return {"message": "Not implemented"}


@router.post("/logout")
async def logout():
    """Logout — add token JTI to Redis blocklist. TODO: Implement."""
    return {"message": "Not implemented"}


@router.post("/refresh")
async def refresh():
    """Refresh JWT token pair. TODO: Implement."""
    return {"message": "Not implemented"}


@router.post("/forgot-password")
async def forgot_password():
    """Request password reset email. TODO: Implement."""
    return {"message": "Not implemented"}


@router.post("/reset-password")
async def reset_password():
    """Submit new password with reset token. TODO: Implement."""
    return {"message": "Not implemented"}


@router.get("/verify-email/{token}")
async def verify_email(token: str):
    """Verify email via token. TODO: Implement."""
    return {"message": "Not implemented"}


@router.get("/csrf-token")
async def csrf_token():
    """Get CSRF token. TODO: Implement."""
    return {"message": "Not implemented"}
