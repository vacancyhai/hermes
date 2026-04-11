"""Rename exam_id column to admission_id in admit_cards, answer_keys, results.

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-11

"""

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("admit_cards", "exam_id", new_column_name="admission_id")
    op.alter_column("answer_keys", "exam_id", new_column_name="admission_id")
    op.alter_column("results", "exam_id", new_column_name="admission_id")


def downgrade() -> None:
    op.alter_column("admit_cards", "admission_id", new_column_name="exam_id")
    op.alter_column("answer_keys", "admission_id", new_column_name="exam_id")
    op.alter_column("results", "admission_id", new_column_name="exam_id")
