"""JobAnswerKey model — maps to `job_answer_keys` table."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class JobAnswerKey(Base):
    __tablename__ = "job_answer_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=False, index=True)
    phase_number: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    answer_key_type: Mapped[str] = mapped_column(String(20), nullable=False, default="provisional")
    files: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    objection_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    objection_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    job = relationship("JobVacancy", back_populates="answer_keys")
