"""AnswerKey model — maps to `answer_keys` table."""

from datetime import date

from app.models.base import Base, PhaseDocMixin
from sqlalchemy import Date, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


class AnswerKey(PhaseDocMixin, Base):
    __tablename__ = "answer_keys"

    slug: Mapped[str] = mapped_column(
        String(500), nullable=False, unique=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    answer_key_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="provisional"
    )
    files: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    objection_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    objection_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)

    job = relationship("Job", back_populates="answer_keys")
    admission = relationship("Admission", back_populates="answer_keys")
