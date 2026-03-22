"""UserProfile model — maps to `user_profiles` table."""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(20))
    category: Mapped[str | None] = mapped_column(String(20))
    is_pwd: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_ex_serviceman: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    state: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))
    pincode: Mapped[str | None] = mapped_column(String(10))
    highest_qualification: Mapped[str | None] = mapped_column(String(50))
    education: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    notification_preferences: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    preferred_states: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    preferred_categories: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    followed_organizations: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="profile")
