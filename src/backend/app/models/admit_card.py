"""AdmitCard model — maps to `admit_cards` table."""

from datetime import date

from app.models.base import Base, PhaseDocMixin
from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship


class AdmitCard(PhaseDocMixin, Base):
    __tablename__ = "admit_cards"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    download_url: Mapped[str] = mapped_column(Text, nullable=False)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    job = relationship("Job", back_populates="admit_cards")
    exam = relationship("EntranceExam", back_populates="admit_cards")
