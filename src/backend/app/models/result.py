"""Result model — maps to `results` table."""

from datetime import date

from app.models.base import Base, PhaseDocMixin
from sqlalchemy import Date, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Result(PhaseDocMixin, Base):
    __tablename__ = "results"

    slug: Mapped[str] = mapped_column(
        String(500), nullable=False, unique=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    links: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    job = relationship("Job", back_populates="results")
    admission = relationship("Admission", back_populates="results")
