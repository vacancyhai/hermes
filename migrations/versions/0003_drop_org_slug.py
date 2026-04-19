"""Drop slug column from organizations table.

Revision ID: 0003_drop_org_slug
Revises: 0002_organizations
Create Date: 2026-04-19
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_drop_org_slug"
down_revision = "0002_organizations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("idx_organizations_slug", table_name="organizations")
    op.drop_column("organizations", "slug")


def downgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column("slug", sa.String(255), nullable=True),
    )
    op.execute(
        "UPDATE organizations SET slug = lower(regexp_replace("
        "regexp_replace(name, '[^a-zA-Z0-9\\s]', '', 'g'), '\\s+', '-', 'g'))"
    )
    op.alter_column("organizations", "slug", nullable=False)
    op.create_unique_constraint("organizations_slug_key", "organizations", ["slug"])
    op.create_index("idx_organizations_slug", "organizations", ["slug"])
