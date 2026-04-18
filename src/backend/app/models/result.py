"""Result model — maps to `results` table."""

from app.models.base import Base, PhaseDocMixin
from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Result(PhaseDocMixin, Base):
    __tablename__ = "results"

    slug: Mapped[str] = mapped_column(
        String(500), nullable=False, unique=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    result_type: Mapped[str] = mapped_column(String(20), nullable=False)
    cutoff_marks: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    total_qualified: Mapped[int | None] = mapped_column(Integer, nullable=True)

    job = relationship("Job", back_populates="results")
    admission = relationship("Admission", back_populates="results")
