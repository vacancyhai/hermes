"""Add organization_id FK to admissions table.

Revision ID: 0004_admissions_organization_id
Revises: 0003_drop_org_slug
Create Date: 2026-04-19
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004_admissions_organization_id"
down_revision = "0003_drop_org_slug"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "admissions",
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("idx_admissions_organization_id", "admissions", ["organization_id"])


def downgrade() -> None:
    op.drop_index("idx_admissions_organization_id", table_name="admissions")
    op.drop_column("admissions", "organization_id")
