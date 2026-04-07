"""Remove is_featured and is_urgent columns from jobs and entrance_exams.

Revision ID: 0003_remove_is_featured_is_urgent
Revises: 0002_add_followed_organizations
Create Date: 2026-04-07
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_drop_featured_urgent"
down_revision = "0002_add_followed_organizations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("jobs", "is_featured")
    op.drop_column("jobs", "is_urgent")
    op.drop_column("entrance_exams", "is_featured")


def downgrade() -> None:
    op.add_column(
        "entrance_exams",
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "jobs",
        sa.Column("is_urgent", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "jobs",
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
