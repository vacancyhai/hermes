"""Pydantic schemas for application tracking endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ApplicationCreateRequest(BaseModel):
    job_id: uuid.UUID
    application_number: str | None = None
    is_priority: bool = False
    notes: str | None = None
    status: str | None = "applied"


class ApplicationUpdateRequest(BaseModel):
    status: str | None = None
    application_number: str | None = None
    is_priority: bool | None = None
    notes: str | None = None


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    application_number: str | None
    is_priority: bool
    applied_on: datetime
    status: str
    notes: str | None
    reminders: list
    result_info: dict
    updated_at: datetime

    model_config = {"from_attributes": True}
