"""Pydantic schemas for authentication endpoints."""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

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


_PHONE_PATTERN = r"^\+\d{10,15}$"

# --- Email OTP verification (email/password registration) ---


class EmailOTPRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(None, pattern=_PHONE_PATTERN)  # E.164 format


class EmailOTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)


class OTPVerifiedResponse(BaseModel):
    verified: bool
    verification_token: str  # Short-lived token to complete registration


def validate_password_strength(password: str) -> str:
    """Validate password meets security requirements."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("Password must contain at least one special character")
    return password


class CompleteRegistrationRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    verification_token: str
    phone: str | None = Field(default=None, pattern=_PHONE_PATTERN)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_strength(v)  # Optional phone


class FirebaseCustomTokenResponse(BaseModel):
    custom_token: str


class CheckUserProvidersRequest(BaseModel):
    email: EmailStr


class UserProvidersResponse(BaseModel):
    exists: bool
    has_password: bool = False
    providers: list[str] = []
    can_add_password: bool = False


class AddPasswordRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    verification_token: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_strength(v)  # Requires OTP verification for security


class CheckPhoneRequest(BaseModel):
    phone: str = Field(pattern=_PHONE_PATTERN)  # E.164 format


class PhoneAvailabilityResponse(BaseModel):
    available: bool
    message: str
    registered: bool


class UpdatePhoneRequest(BaseModel):
    phone: str = Field(pattern=_PHONE_PATTERN)  # E.164 format


class VerifyPhoneRequest(BaseModel):
    firebase_id_token: str  # Firebase ID token obtained after client-side phone auth


class SetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_strength(v)


class ChangePasswordRequest(BaseModel):
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_strength(v)


class LinkEmailPasswordRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_strength(v)


# --- Admin/Operator schemas (unchanged — local bcrypt + JWT) ---


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminUserUpdateRequest(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    phone: str | None = None
    department: str | None = None
    role: str | None = None
    status: str | None = None


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
