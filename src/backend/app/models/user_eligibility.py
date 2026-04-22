"""Pre-computed eligibility tables — one row per (user, job) and (user, admission).

Populated asynchronously by Celery tasks triggered on:
  - Profile save/update  → recompute all active jobs + admissions for that user
  - Job create/update    → recompute all users for that job
  - Admission create/update → recompute all users for that admission

Eligibility endpoints read from these tables first; fall back to live compute
if a row is missing (e.g. task not yet run for a new user).
"""

import uuid
from datetime import datetime

from app.models.base import Base
from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column


class UserJobEligibility(Base):
    __tablename__ = "job_eligibility"
    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_job_elig_user_job"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    reasons: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class UserAdmissionEligibility(Base):
    __tablename__ = "admission_eligibility"
    __table_args__ = (
        UniqueConstraint("user_id", "admission_id", name="uq_adm_elig_user_admission"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    admission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    reasons: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
