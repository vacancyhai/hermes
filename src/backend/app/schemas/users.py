"""Pydantic schemas for user profile endpoints."""

import uuid
from datetime import date, datetime
from typing import Literal

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
    preferred_states: list
    preferred_categories: list
    followed_organizations: list
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileUpdateRequest(BaseModel):
    date_of_birth: date | None = None
    gender: Literal["Male", "Female", "Other"] | None = None
    category: Literal["General", "OBC", "SC", "ST", "EWS", "EBC"] | None = None
    is_pwd: bool | None = None
    is_ex_serviceman: bool | None = None
    state: str | None = None
    city: str | None = None
    pincode: str | None = None
    highest_qualification: Literal["10th", "12th", "diploma", "graduate", "postgraduate", "phd"] | None = None
    education: dict | None = None
    notification_preferences: dict | None = None
    preferred_states: list | None = None
    preferred_categories: list | None = None


class PhoneUpdateRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=20)


class FCMTokenRequest(BaseModel):
    token: str = Field(min_length=10, max_length=500)
    device_name: str | None = None


class FCMTokenDeleteRequest(BaseModel):
    token: str = Field(min_length=10, max_length=500)


class NotificationPreferencesRequest(BaseModel):
    email: bool | None = None
    push: bool | None = None
    in_app: bool | None = None
    whatsapp: bool | None = None
