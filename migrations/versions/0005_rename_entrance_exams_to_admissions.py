"""Rename entrance_exams table to admissions.

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-11

"""

from alembic import op

revision = "0005"
down_revision = "0004_remove_views"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("entrance_exams", "admissions")


def downgrade() -> None:
    op.rename_table("admissions", "entrance_exams")
