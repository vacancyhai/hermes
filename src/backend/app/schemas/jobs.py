"""Pydantic schemas for job vacancy endpoints."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

EMPLOYMENT_TYPES = Literal["permanent", "temporary", "contract", "apprentice"]
QUALIFICATION_LEVELS = Literal[
    "10th", "12th", "diploma", "graduate", "postgraduate", "phd"
]
JOB_STATUSES = Literal["upcoming", "active", "inactive", "closed"]
SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


# --- Request schemas ---


class JobCreateRequest(BaseModel):
    job_title: str = Field(min_length=1, max_length=500)
    slug: str = Field(min_length=1, max_length=500, pattern=SLUG_PATTERN)
    organization: str = Field(min_length=1, max_length=255)
    organization_id: uuid.UUID | None = None
    department: str | None = None
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
    links: list = Field(default_factory=list)
    salary: dict = Field(default_factory=dict)
    selection_process: list = Field(default_factory=list)
    fee: dict = Field(default_factory=dict)
    status: JOB_STATUSES = "active"

    @model_validator(mode="after")
    def validate_dates(self) -> "JobCreateRequest":
        if self.application_start and self.application_end:
            if self.application_end <= self.application_start:
                raise ValueError("application_end must be after application_start")
        return self


class JobUpdateRequest(BaseModel):
    job_title: str | None = None
    slug: str | None = Field(None, min_length=1, max_length=500, pattern=SLUG_PATTERN)
    organization: str | None = None
    organization_id: uuid.UUID | None = None
    department: str | None = None
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
    links: list | None = None
    salary: dict | None = None
    selection_process: list | None = None
    fee: dict | None = None
    status: JOB_STATUSES | None = None

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
    organization_id: uuid.UUID | None = None
    department: str | None
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
    links: list
    salary: dict
    selection_process: list
    fee: dict
    status: str
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
    employment_type: str | None
    qualification_level: str | None
    total_vacancies: int | None
    short_description: str | None
    application_end: date | None
    notification_date: date | None = None
    exam_start: date | None = None
    result_date: date | None = None
    fee: dict = Field(default_factory=dict)
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Admit Card schemas ────────────────────────────────────────────────────────


class AdmitCardCreateRequest(BaseModel):
    job_id: uuid.UUID | None = None
    admission_id: uuid.UUID | None = None
    slug: str = Field(min_length=1, max_length=500, pattern=SLUG_PATTERN)
    title: str = Field(min_length=1, max_length=255)
    links: list[dict] = Field(default_factory=list)
    exam_start: date | None = None
    exam_end: date | None = None
    published_at: datetime | None = None


class AdmitCardUpdateRequest(BaseModel):
    slug: str | None = Field(None, min_length=1, max_length=500, pattern=SLUG_PATTERN)
    title: str | None = Field(None, min_length=1, max_length=255)
    links: list[dict] | None = None
    exam_start: date | None = None
    exam_end: date | None = None
    published_at: datetime | None = None


class AdmitCardResponse(BaseModel):
    id: uuid.UUID
    slug: str
    job_id: uuid.UUID | None
    admission_id: uuid.UUID | None
    title: str
    links: list
    exam_start: date | None
    exam_end: date | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Answer Key schemas ────────────────────────────────────────────────────────


class AnswerKeyCreateRequest(BaseModel):
    job_id: uuid.UUID | None = None
    admission_id: uuid.UUID | None = None
    slug: str = Field(min_length=1, max_length=500, pattern=SLUG_PATTERN)
    title: str = Field(min_length=1, max_length=255)
    links: list[dict] = Field(default_factory=list)
    start_date: date | None = None
    end_date: date | None = None
    published_at: datetime | None = None


class AnswerKeyUpdateRequest(BaseModel):
    slug: str | None = Field(None, min_length=1, max_length=500, pattern=SLUG_PATTERN)
    title: str | None = Field(None, min_length=1, max_length=255)
    links: list[dict] | None = None
    start_date: date | None = None
    end_date: date | None = None
    published_at: datetime | None = None


class AnswerKeyResponse(BaseModel):
    id: uuid.UUID
    slug: str
    job_id: uuid.UUID | None
    admission_id: uuid.UUID | None
    title: str
    links: list
    start_date: date | None
    end_date: date | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Result schemas ────────────────────────────────────────────────────────────


class ResultCreateRequest(BaseModel):
    job_id: uuid.UUID | None = None
    admission_id: uuid.UUID | None = None
    slug: str = Field(min_length=1, max_length=500, pattern=SLUG_PATTERN)
    title: str = Field(min_length=1, max_length=255)
    links: list[dict] = Field(default_factory=list)
    start_date: date | None = None
    end_date: date | None = None
    published_at: datetime | None = None


class ResultUpdateRequest(BaseModel):
    slug: str | None = Field(None, min_length=1, max_length=500, pattern=SLUG_PATTERN)
    title: str | None = Field(None, min_length=1, max_length=255)
    links: list[dict] | None = None
    start_date: date | None = None
    end_date: date | None = None
    published_at: datetime | None = None


class ResultResponse(BaseModel):
    id: uuid.UUID
    slug: str
    job_id: uuid.UUID | None
    admission_id: uuid.UUID | None
    title: str
    links: list
    start_date: date | None
    end_date: date | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
