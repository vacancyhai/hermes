"""Pydantic schemas for authentication endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# --- Firebase Auth (user) ---

class FirebaseVerifyRequest(BaseModel):
    id_token: str
    full_name: str | None = None  # Used for first-time registration


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class MessageResponse(BaseModel):
    message: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str | None
    full_name: str
    phone: str | None
    status: str
    is_email_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Admin/Operator schemas (unchanged — local bcrypt + JWT) ---

class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminUserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    phone: str | None
    role: str
    department: str | None
    status: str
    is_email_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}
