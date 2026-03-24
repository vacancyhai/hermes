"""EntranceExam model — maps to `entrance_exams` table."""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class EntranceExam(Base):
    __tablename__ = "entrance_exams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    exam_name: Mapped[str] = mapped_column(String(500), nullable=False)
    conducting_body: Mapped[str] = mapped_column(String(255), nullable=False)
    counselling_body: Mapped[str | None] = mapped_column(String(255), nullable=True)
    exam_type: Mapped[str] = mapped_column(String(20), nullable=False, default="pg")
    stream: Mapped[str] = mapped_column(String(30), nullable=False, default="general")
    eligibility: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    exam_details: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    selection_process: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    seats_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    application_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    application_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    exam_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    result_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    counselling_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    fee_general: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fee_obc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fee_sc_st: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fee_ews: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fee_female: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    admit_cards = relationship("JobAdmitCard", back_populates="exam", cascade="all, delete-orphan", order_by="JobAdmitCard.phase_number")
    answer_keys = relationship("JobAnswerKey", back_populates="exam", cascade="all, delete-orphan", order_by="JobAnswerKey.phase_number")
    results = relationship("JobResult", back_populates="exam", cascade="all, delete-orphan", order_by="JobResult.phase_number")
