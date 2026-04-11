"""Result model — maps to `results` table."""

from app.models.base import Base, PhaseDocMixin
from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Result(PhaseDocMixin, Base):
    __tablename__ = "results"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    result_type: Mapped[str] = mapped_column(String(20), nullable=False)
    download_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    cutoff_marks: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    total_qualified: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    job = relationship("Job", back_populates="results")
    admission = relationship("Admission", back_populates="results")
