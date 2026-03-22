"""User profile endpoints (requires user JWT).

GET  /api/v1/users/profile               — Get own profile
PUT  /api/v1/users/profile               — Update own profile
PUT  /api/v1/users/profile/phone         — Update phone number
GET  /api/v1/users/me/following           — List followed organizations
POST /api/v1/organizations/{name}/follow  — Follow an organization
DELETE /api/v1/organizations/{name}/follow — Unfollow an organization
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user_profile import UserProfile
from app.schemas.auth import UserResponse
from app.schemas.users import PhoneUpdateRequest, ProfileResponse, ProfileUpdateRequest

router = APIRouter(tags=["users"])

MAX_FOLLOWED_ORGS = 50


@router.get("/api/v1/users/profile")
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


@router.put("/api/v1/users/profile")
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


@router.put("/api/v1/users/profile/phone")
async def update_phone(
    body: PhoneUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update phone number on user record."""
    user, _ = current_user
    user.phone = body.phone
    return {"message": "Phone number updated", "phone": user.phone}


@router.get("/api/v1/users/me/following")
async def list_following(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List organizations the user follows."""
    user, _ = current_user
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    orgs = profile.followed_organizations if profile else []
    return {"followed_organizations": orgs, "count": len(orgs)}


@router.post("/api/v1/organizations/{name}/follow", status_code=status.HTTP_200_OK)
async def follow_organization(
    name: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Follow an organization. Idempotent — returns 200 if already following."""
    user, _ = current_user
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    orgs = list(profile.followed_organizations or [])
    name_lower = name.strip().lower()

    if name_lower in [o.lower() for o in orgs]:
        return {"message": f"Already following {name}", "followed_organizations": orgs}

    if len(orgs) >= MAX_FOLLOWED_ORGS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_FOLLOWED_ORGS} organizations allowed",
        )

    orgs.append(name.strip())
    profile.followed_organizations = orgs
    return {"message": f"Now following {name}", "followed_organizations": orgs}


@router.delete("/api/v1/organizations/{name}/follow")
async def unfollow_organization(
    name: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unfollow an organization."""
    user, _ = current_user
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    orgs = list(profile.followed_organizations or [])
    name_lower = name.strip().lower()
    new_orgs = [o for o in orgs if o.lower() != name_lower]

    if len(new_orgs) == len(orgs):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Not following {name}")

    profile.followed_organizations = new_orgs
    return {"message": f"Unfollowed {name}", "followed_organizations": new_orgs}
