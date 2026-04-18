"""AdmitCard model — maps to `admit_cards` table."""

from datetime import date

from app.models.base import Base, PhaseDocMixin
from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class AdmitCard(PhaseDocMixin, Base):
    __tablename__ = "admit_cards"

    slug: Mapped[str] = mapped_column(
        String(500), nullable=False, unique=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    exam_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    exam_end: Mapped[date | None] = mapped_column(Date, nullable=True)

    job = relationship("Job", back_populates="admit_cards")
    admission = relationship("Admission", back_populates="admit_cards")
