"""Rename exam_name/exam_type/exam_date/exam_details → admission_name/admission_type/admission_date/admission_details in admissions table.

Revision ID: 0007_rename_admission_columns
Revises: 0006
Create Date: 2026-04-11
"""

from alembic import op

revision = "0007_rename_admission_columns"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("admissions", "exam_name", new_column_name="admission_name")
    op.alter_column("admissions", "exam_type", new_column_name="admission_type")
    op.alter_column("admissions", "exam_date", new_column_name="admission_date")
    op.alter_column("admissions", "exam_details", new_column_name="admission_details")


def downgrade() -> None:
    op.alter_column("admissions", "admission_name", new_column_name="exam_name")
    op.alter_column("admissions", "admission_type", new_column_name="exam_type")
    op.alter_column("admissions", "admission_date", new_column_name="exam_date")
    op.alter_column("admissions", "admission_details", new_column_name="exam_details")
