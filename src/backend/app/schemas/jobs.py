"""Pydantic schemas for job vacancy endpoints."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

EMPLOYMENT_TYPES = Literal["permanent", "temporary", "contract", "apprentice"]
QUALIFICATION_LEVELS = Literal[
    "10th", "12th", "diploma", "graduate", "postgraduate", "phd"
]
JOB_STATUSES = Literal["draft", "active", "expired", "cancelled", "upcoming"]


# --- Request schemas ---


class JobCreateRequest(BaseModel):
    job_title: str = Field(min_length=1, max_length=500)
    organization: str = Field(min_length=1, max_length=255)
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
    salary: dict = Field(default_factory=dict)
    selection_process: list = Field(default_factory=list)
    fee_general: int | None = None
    fee_obc: int | None = None
    fee_sc_st: int | None = None
    fee_ews: int | None = None
    fee_female: int | None = None
    status: JOB_STATUSES = "draft"

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
    fee_general: int | None = None
    fee_obc: int | None = None
    fee_sc_st: int | None = None
    fee_ews: int | None = None
    fee_female: int | None = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Admit Card schemas ────────────────────────────────────────────────────────


class AdmitCardCreateRequest(BaseModel):
    job_id: uuid.UUID | None = None
    admission_id: uuid.UUID | None = None
    phase_number: int | None = Field(None, ge=1, le=10)
    title: str = Field(min_length=1, max_length=255)
    download_url: str = Field(min_length=1)
    valid_from: date | None = None
    valid_until: date | None = None
    notes: str | None = None
    published_at: datetime | None = None


class AdmitCardUpdateRequest(BaseModel):
    phase_number: int | None = None
    title: str | None = Field(None, min_length=1, max_length=255)
    download_url: str | None = None
    valid_from: date | None = None
    valid_until: date | None = None
    notes: str | None = None
    published_at: datetime | None = None


class AdmitCardResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID | None
    admission_id: uuid.UUID | None
    phase_number: int | None
    title: str
    download_url: str
    valid_from: date | None
    valid_until: date | None
    notes: str | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Answer Key schemas ────────────────────────────────────────────────────────

ANSWER_KEY_TYPES = Literal["provisional", "final"]


class AnswerKeyCreateRequest(BaseModel):
    job_id: uuid.UUID | None = None
    admission_id: uuid.UUID | None = None
    phase_number: int | None = Field(None, ge=1, le=10)
    title: str = Field(min_length=1, max_length=255)
    answer_key_type: ANSWER_KEY_TYPES = "provisional"
    files: list[dict] = Field(default_factory=list)
    objection_url: str | None = None
    objection_deadline: date | None = None
    published_at: datetime | None = None


class AnswerKeyUpdateRequest(BaseModel):
    phase_number: int | None = None
    title: str | None = Field(None, min_length=1, max_length=255)
    answer_key_type: ANSWER_KEY_TYPES | None = None
    files: list[dict] | None = None
    objection_url: str | None = None
    objection_deadline: date | None = None
    published_at: datetime | None = None


class AnswerKeyResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID | None
    admission_id: uuid.UUID | None
    phase_number: int | None
    title: str
    answer_key_type: str
    files: list
    objection_url: str | None
    objection_deadline: date | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Result schemas ────────────────────────────────────────────────────────────

RESULT_TYPES = Literal["shortlist", "cutoff", "merit_list", "final"]


class ResultCreateRequest(BaseModel):
    job_id: uuid.UUID | None = None
    admission_id: uuid.UUID | None = None
    phase_number: int | None = Field(None, ge=1, le=10)
    title: str = Field(min_length=1, max_length=255)
    result_type: RESULT_TYPES
    download_url: str | None = None
    cutoff_marks: dict | None = None
    total_qualified: int | None = Field(None, ge=0)
    notes: str | None = None
    published_at: datetime | None = None


class ResultUpdateRequest(BaseModel):
    phase_number: int | None = None
    title: str | None = Field(None, min_length=1, max_length=255)
    result_type: RESULT_TYPES | None = None
    download_url: str | None = None
    cutoff_marks: dict | None = None
    total_qualified: int | None = Field(None, ge=0)
    notes: str | None = None
    published_at: datetime | None = None


class ResultResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID | None
    admission_id: uuid.UUID | None
    phase_number: int | None
    title: str
    result_type: str
    download_url: str | None
    cutoff_marks: dict | None
    total_qualified: int | None
    notes: str | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
