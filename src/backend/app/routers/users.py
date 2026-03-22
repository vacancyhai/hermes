"""User profile endpoints (requires user JWT).

GET /api/v1/users/profile       — Get own profile
PUT /api/v1/users/profile       — Update own profile
PUT /api/v1/users/profile/phone — Update phone number
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user_profile import UserProfile
from app.schemas.auth import UserResponse
from app.schemas.users import PhoneUpdateRequest, ProfileResponse, ProfileUpdateRequest

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/profile")
async def get_profile(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get own user data and profile."""
    user, _ = current_user

    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()

    user_data = UserResponse.model_validate(user).model_dump()
    if profile:
        user_data["profile"] = ProfileResponse.model_validate(profile).model_dump()

    return user_data


@router.put("/profile")
async def update_profile(
    body: ProfileUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update own profile fields."""
    user, _ = current_user

    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    return ProfileResponse.model_validate(profile).model_dump()


@router.put("/profile/phone")
async def update_phone(
    body: PhoneUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update phone number on user record."""
    user, _ = current_user
    user.phone = body.phone
    return {"message": "Phone number updated", "phone": user.phone}
