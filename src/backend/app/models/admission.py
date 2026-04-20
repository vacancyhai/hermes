"""Admission model — maps to `admissions` table."""

import uuid
from datetime import date, datetime

from app.models.base import Base
from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

_CASCADE_ALL_DELETE = "all, delete-orphan"


class Admission(Base):
    __tablename__ = "admissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    admission_name: Mapped[str] = mapped_column(String(500), nullable=False)
    conducting_body: Mapped[str] = mapped_column(String(255), nullable=False)
    counselling_body: Mapped[str | None] = mapped_column(String(255), nullable=True)
    admission_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pg"
    )
    stream: Mapped[str] = mapped_column(String(30), nullable=False, default="general")
    eligibility: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default="{}"
    )
    admission_details: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default="{}"
    )
    selection_process: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    seats_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    application_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    application_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    admission_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    exam_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    exam_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    result_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    counselling_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    fee: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    organization_ref = relationship(
        "Organization",
        back_populates="admissions",
        foreign_keys=[organization_id],
    )
    admit_cards = relationship(
        "AdmitCard",
        back_populates="admission",
        cascade=_CASCADE_ALL_DELETE,
        order_by="AdmitCard.created_at",
    )
    answer_keys = relationship(
        "AnswerKey",
        back_populates="admission",
        cascade=_CASCADE_ALL_DELETE,
        order_by="AnswerKey.created_at",
    )
    results = relationship(
        "Result",
        back_populates="admission",
        cascade=_CASCADE_ALL_DELETE,
        order_by="Result.created_at",
    )
