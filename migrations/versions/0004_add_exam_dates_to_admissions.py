"""Add exam_start/exam_end to admissions; rename valid_from/valid_until to exam_start/exam_end in admit_cards.

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # admissions: add exam date range columns
    op.add_column("admissions", sa.Column("exam_start", sa.Date(), nullable=True))
    op.add_column("admissions", sa.Column("exam_end", sa.Date(), nullable=True))

    # admit_cards: rename valid_from/valid_until to exam_start/exam_end
    op.alter_column("admit_cards", "valid_from", new_column_name="exam_start")
    op.alter_column("admit_cards", "valid_until", new_column_name="exam_end")


def downgrade() -> None:
    # admit_cards: restore original column names
    op.alter_column("admit_cards", "exam_start", new_column_name="valid_from")
    op.alter_column("admit_cards", "exam_end", new_column_name="valid_until")

    # admissions: drop added columns
    op.drop_column("admissions", "exam_end")
    op.drop_column("admissions", "exam_start")
