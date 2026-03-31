"""Job model — maps to `jobs` table."""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    organization: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    department: Mapped[str | None] = mapped_column(String(255))
    employment_type: Mapped[str | None] = mapped_column(String(50), default="permanent")
    qualification_level: Mapped[str | None] = mapped_column(String(50), index=True)
    total_vacancies: Mapped[int | None] = mapped_column(Integer)
    vacancy_breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    description: Mapped[str | None] = mapped_column(Text)
    short_description: Mapped[str | None] = mapped_column(Text)
    eligibility: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    application_details: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    documents: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    source_url: Mapped[str | None] = mapped_column(Text)
    notification_date: Mapped[date | None] = mapped_column(Date)
    application_start: Mapped[date | None] = mapped_column(Date)
    application_end: Mapped[date | None] = mapped_column(Date, index=True)
    exam_start: Mapped[date | None] = mapped_column(Date)
    exam_end: Mapped[date | None] = mapped_column(Date)
    result_date: Mapped[date | None] = mapped_column(Date)
    exam_details: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    salary_initial: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    salary: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    selection_process: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    fee_general: Mapped[int | None] = mapped_column(Integer)
    fee_obc: Mapped[int | None] = mapped_column(Integer)
    fee_sc_st: Mapped[int | None] = mapped_column(Integer)
    fee_ews: Mapped[int | None] = mapped_column(Integer)
    fee_female: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_urgent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("admin_users.id"))
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
    source_pdf_path: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    admit_cards = relationship("AdmitCard", back_populates="job", cascade="all, delete-orphan", order_by="AdmitCard.phase_number")
    answer_keys = relationship("AnswerKey", back_populates="job", cascade="all, delete-orphan", order_by="AnswerKey.phase_number")
    results = relationship("Result", back_populates="job", cascade="all, delete-orphan", order_by="Result.phase_number")
