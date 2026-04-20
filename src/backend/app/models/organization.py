"""Organization model — maps to `organizations` table."""

import uuid
from datetime import datetime

from app.models.base import Base
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

_ORG_TYPES = ("jobs", "admissions", "both")


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    slug: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    org_type: Mapped[str] = mapped_column(String(20), nullable=False, default="both")
    short_name: Mapped[str | None] = mapped_column(String(50))
    logo_url: Mapped[str | None] = mapped_column(Text)
    website_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    jobs = relationship(
        "Job", back_populates="organization_ref", foreign_keys="Job.organization_id"
    )
    admissions = relationship(
        "Admission",
        back_populates="organization_ref",
        foreign_keys="Admission.organization_id",
    )
