"""Pydantic schemas for admission endpoints."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

EXAM_TYPES = Literal["ug", "pg", "doctoral", "lateral"]
EXAM_STREAMS = Literal[
    "medical", "engineering", "law", "management", "arts_science", "general"
]
EXAM_STATUSES = Literal["upcoming", "active", "completed", "cancelled"]


class AdmissionCreateRequest(BaseModel):
    exam_name: str = Field(min_length=1, max_length=500)
    conducting_body: str = Field(min_length=1, max_length=255)
    counselling_body: str | None = None
    exam_type: EXAM_TYPES = "pg"
    stream: EXAM_STREAMS = "general"
    eligibility: dict = Field(default_factory=dict)
    exam_details: dict = Field(default_factory=dict)
    selection_process: list = Field(default_factory=list)
    seats_info: dict | None = None
    application_start: date | None = None
    application_end: date | None = None
    exam_date: date | None = None
    result_date: date | None = None
    counselling_start: date | None = None
    fee_general: int | None = None
    fee_obc: int | None = None
    fee_sc_st: int | None = None
    fee_ews: int | None = None
    fee_female: int | None = None
    description: str | None = None
    short_description: str | None = None
    source_url: str | None = None
    status: EXAM_STATUSES = "active"


class AdmissionUpdateRequest(BaseModel):
    exam_name: str | None = Field(None, min_length=1, max_length=500)
    conducting_body: str | None = None
    counselling_body: str | None = None
    exam_type: EXAM_TYPES | None = None
    stream: EXAM_STREAMS | None = None
    eligibility: dict | None = None
    exam_details: dict | None = None
    selection_process: list | None = None
    seats_info: dict | None = None
    application_start: date | None = None
    application_end: date | None = None
    exam_date: date | None = None
    result_date: date | None = None
    counselling_start: date | None = None
    fee_general: int | None = None
    fee_obc: int | None = None
    fee_sc_st: int | None = None
    fee_ews: int | None = None
    fee_female: int | None = None
    description: str | None = None
    short_description: str | None = None
    source_url: str | None = None
    status: EXAM_STATUSES | None = None


class AdmissionResponse(BaseModel):
    id: uuid.UUID
    slug: str
    exam_name: str
    conducting_body: str
    counselling_body: str | None
    exam_type: str
    stream: str
    eligibility: dict
    exam_details: dict
    selection_process: list
    seats_info: dict | None
    application_start: date | None
    application_end: date | None
    exam_date: date | None
    result_date: date | None
    counselling_start: date | None
    fee_general: int | None
    fee_obc: int | None
    fee_sc_st: int | None
    fee_ews: int | None
    fee_female: int | None
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
    slug: str
    exam_name: str
    conducting_body: str
    counselling_body: str | None
    exam_type: str
    stream: str
    short_description: str | None
    application_end: date | None
    exam_date: date | None
    result_date: date | None
    fee_general: int | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
