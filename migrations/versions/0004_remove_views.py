"""Remove views column from jobs and entrance_exams tables.

Revision ID: 0004_remove_views
Revises: 0003_drop_featured_urgent
Create Date: 2026-04-07
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_remove_views"
down_revision = "0003_drop_featured_urgent"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("jobs", "views")
    op.drop_column("entrance_exams", "views")


def downgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("views", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "entrance_exams",
        sa.Column("views", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
