"""Result model — maps to `results` table."""

import uuid
from datetime import datetime
from typing import Optional

from app.models.base import Base
from sqlalchemy import DateTime, ForeignKey, Integer, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Result(Base):
    __tablename__ = "results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    exam_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entrance_exams.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    phase_number: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    result_type: Mapped[str] = mapped_column(String(20), nullable=False)
    download_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    cutoff_marks: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    total_qualified: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    job = relationship("Job", back_populates="results")
    exam = relationship("EntranceExam", back_populates="results")
