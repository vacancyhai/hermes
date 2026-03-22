"""Pydantic schemas for user profile endpoints."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class ProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    date_of_birth: date | None
    gender: str | None
    category: str | None
    is_pwd: bool
    is_ex_serviceman: bool
    state: str | None
    city: str | None
    pincode: str | None
    highest_qualification: str | None
    education: dict
    notification_preferences: dict
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileUpdateRequest(BaseModel):
    date_of_birth: date | None = None
    gender: str | None = None
    category: str | None = None
    is_pwd: bool | None = None
    is_ex_serviceman: bool | None = None
    state: str | None = None
    city: str | None = None
    pincode: str | None = None
    highest_qualification: str | None = None
    education: dict | None = None
    notification_preferences: dict | None = None


class PhoneUpdateRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=20)
