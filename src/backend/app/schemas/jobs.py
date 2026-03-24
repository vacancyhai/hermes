"""Pydantic schemas for job vacancy endpoints."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

JOB_TYPES = Literal["latest_job", "result", "admit_card", "answer_key", "admission", "yojana"]
EMPLOYMENT_TYPES = Literal["permanent", "temporary", "contract", "apprentice"]
QUALIFICATION_LEVELS = Literal["10th", "12th", "diploma", "graduate", "postgraduate", "phd"]
JOB_STATUSES = Literal["draft", "active", "expired", "cancelled", "upcoming"]


# --- Request schemas ---

class JobCreateRequest(BaseModel):
    job_title: str = Field(min_length=1, max_length=500)
    organization: str = Field(min_length=1, max_length=255)
    department: str | None = None
    job_type: JOB_TYPES = "latest_job"
    employment_type: EMPLOYMENT_TYPES | None = "permanent"
    qualification_level: QUALIFICATION_LEVELS | None = None
    total_vacancies: int | None = None
    vacancy_breakdown: dict = Field(default_factory=dict)
    description: str | None = None
    short_description: str | None = None
    eligibility: dict = Field(default_factory=dict)
    application_details: dict = Field(default_factory=dict)
    documents: list = Field(default_factory=list)
    source_url: str | None = None
    notification_date: date | None = None
    application_start: date | None = None
    application_end: date | None = None
    exam_start: date | None = None
    exam_end: date | None = None
    result_date: date | None = None
    exam_details: dict = Field(default_factory=dict)
    salary_initial: int | None = None
    salary_max: int | None = None
    salary: dict = Field(default_factory=dict)
    selection_process: list = Field(default_factory=list)
    fee_general: int | None = None
    fee_obc: int | None = None
    fee_sc_st: int | None = None
    fee_ews: int | None = None
    fee_female: int | None = None
    status: JOB_STATUSES = "draft"
    is_featured: bool = False
    is_urgent: bool = False

    @model_validator(mode="after")
    def validate_dates(self) -> "JobCreateRequest":
        if self.application_start and self.application_end:
            if self.application_end <= self.application_start:
                raise ValueError("application_end must be after application_start")
        return self


class JobUpdateRequest(BaseModel):
    job_title: str | None = None
    organization: str | None = None
    department: str | None = None
    job_type: JOB_TYPES | None = None
    employment_type: EMPLOYMENT_TYPES | None = None
    qualification_level: QUALIFICATION_LEVELS | None = None
    total_vacancies: int | None = None
    vacancy_breakdown: dict | None = None
    description: str | None = None
    short_description: str | None = None
    eligibility: dict | None = None
    application_details: dict | None = None
    documents: list | None = None
    source_url: str | None = None
    notification_date: date | None = None
    application_start: date | None = None
    application_end: date | None = None
    exam_start: date | None = None
    exam_end: date | None = None
    result_date: date | None = None
    exam_details: dict | None = None
    salary_initial: int | None = None
    salary_max: int | None = None
    salary: dict | None = None
    selection_process: list | None = None
    fee_general: int | None = None
    fee_obc: int | None = None
    fee_sc_st: int | None = None
    fee_ews: int | None = None
    fee_female: int | None = None
    status: JOB_STATUSES | None = None
    is_featured: bool | None = None
    is_urgent: bool | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "JobUpdateRequest":
        if self.application_start and self.application_end:
            if self.application_end <= self.application_start:
                raise ValueError("application_end must be after application_start")
        return self


# --- Response schemas ---

class JobResponse(BaseModel):
    id: uuid.UUID
    job_title: str
    slug: str
    organization: str
    department: str | None
    job_type: str
    employment_type: str | None
    qualification_level: str | None
    total_vacancies: int | None
    vacancy_breakdown: dict
    description: str | None
    short_description: str | None
    eligibility: dict
    application_details: dict
    documents: list
    source_url: str | None
    notification_date: date | None
    application_start: date | None
    application_end: date | None
    exam_start: date | None
    exam_end: date | None
    result_date: date | None
    exam_details: dict
    salary_initial: int | None
    salary_max: int | None
    salary: dict
    selection_process: list
    fee_general: int | None
    fee_obc: int | None
    fee_sc_st: int | None
    fee_ews: int | None
    fee_female: int | None
    status: str
    is_featured: bool
    is_urgent: bool
    views: int
    applications_count: int
    source: str
    source_pdf_path: str | None = None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobListItem(BaseModel):
    id: uuid.UUID
    job_title: str
    slug: str
    organization: str
    department: str | None
    job_type: str
    employment_type: str | None
    qualification_level: str | None
    total_vacancies: int | None
    short_description: str | None
    application_end: date | None
    fee_general: int | None = None
    fee_obc: int | None = None
    fee_sc_st: int | None = None
    fee_ews: int | None = None
    fee_female: int | None = None
    status: str
    is_featured: bool
    is_urgent: bool
    views: int
    applications_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel):
    data: list
    pagination: dict
