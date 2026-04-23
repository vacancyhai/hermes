"""Pydantic schemas for admission endpoints."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field  # noqa: F401

ADMISSION_TYPES = Literal["ug", "pg", "doctoral", "lateral"]
ADMISSION_STREAMS = Literal[
    "medical", "engineering", "law", "management", "arts_science", "general"
]
ADMISSION_STATUSES = Literal["upcoming", "active", "inactive", "closed"]


class AdmissionCreateRequest(BaseModel):
    organization_id: uuid.UUID | None = None
    admission_name: str = Field(min_length=1, max_length=500)
    slug: str | None = Field(
        None, min_length=1, max_length=500, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    conducting_body: str = Field(min_length=1, max_length=255)
    counselling_body: str | None = None
    admission_type: ADMISSION_TYPES = "pg"
    stream: ADMISSION_STREAMS = "general"
    eligibility: dict = Field(default_factory=dict)
    admission_details: dict = Field(default_factory=dict)
    selection_process: list = Field(default_factory=list)
    seats_info: dict | None = None
    application_start: date | None = None
    application_end: date | None = None
    admission_date: date | None = None
    exam_start: date | None = None
    exam_end: date | None = None
    result_date: date | None = None
    counselling_start: date | None = None
    fee: dict = Field(default_factory=dict)
    description: str | None = None
    short_description: str | None = None
    source_url: str | None = None
    status: ADMISSION_STATUSES = "active"


class AdmissionUpdateRequest(BaseModel):
    organization_id: uuid.UUID | None = None
    admission_name: str | None = Field(None, min_length=1, max_length=500)
    slug: str | None = Field(
        None, min_length=1, max_length=500, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    conducting_body: str | None = None
    counselling_body: str | None = None
    admission_type: ADMISSION_TYPES | None = None
    stream: ADMISSION_STREAMS | None = None
    eligibility: dict | None = None
    admission_details: dict | None = None
    selection_process: list | None = None
    seats_info: dict | None = None
    application_start: date | None = None
    application_end: date | None = None
    admission_date: date | None = None
    exam_start: date | None = None
    exam_end: date | None = None
    result_date: date | None = None
    counselling_start: date | None = None
    fee: dict | None = None
    description: str | None = None
    short_description: str | None = None
    source_url: str | None = None
    status: ADMISSION_STATUSES | None = None


class AdmissionResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID | None = None
    slug: str
    admission_name: str
    conducting_body: str
    counselling_body: str | None
    admission_type: str
    stream: str
    eligibility: dict
    admission_details: dict
    selection_process: list
    seats_info: dict | None
    application_start: date | None
    application_end: date | None
    admission_date: date | None
    exam_start: date | None
    exam_end: date | None
    result_date: date | None
    counselling_start: date | None
    fee: dict
    description: str | None
    short_description: str | None
    source_url: str | None
    status: str
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AdmissionListItem(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID | None = None
    slug: str
    admission_name: str
    organization_logo_url: str | None = None
    conducting_body: str
    counselling_body: str | None
    admission_type: str
    stream: str
    short_description: str | None
    application_end: date | None
    admission_date: date | None
    exam_start: date | None
    exam_end: date | None
    result_date: date | None
    fee: dict = Field(default_factory=dict)
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
