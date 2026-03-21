"""UserJobApplication model — maps to `user_job_applications` table."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserJobApplication(Base):
    __tablename__ = "user_job_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=False)
    application_number: Mapped[str | None] = mapped_column(String(100))
    is_priority: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    applied_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="applied")
    notes: Mapped[str | None] = mapped_column(Text)
    reminders: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    result_info: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "job_id"),
    )

    # Relationships
    user = relationship("User", back_populates="applications")
    job = relationship("JobVacancy", back_populates="applications")
