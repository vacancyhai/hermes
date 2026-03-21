"""User profile endpoints.

GET /api/v1/users/profile
PUT /api/v1/users/profile
PUT /api/v1/users/profile/phone
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/profile")
async def get_profile():
    """Get own profile. TODO: Implement."""
    return {"message": "Not implemented"}


@router.put("/profile")
async def update_profile():
    """Update own profile. TODO: Implement."""
    return {"message": "Not implemented"}


@router.put("/profile/phone")
async def update_phone():
    """Update phone number. TODO: Implement."""
    return {"message": "Not implemented"}
