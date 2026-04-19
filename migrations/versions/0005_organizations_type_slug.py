"""Add type and slug to organizations table.

Revision ID: 0005_organizations_type_slug
Revises: 0004_admissions_organization_id
Create Date: 2026-04-19
"""

import sqlalchemy as sa
from alembic import op

revision = "0005_organizations_type_slug"
down_revision = "0004_admissions_organization_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column(
            "org_type",
            sa.String(20),
            nullable=False,
            server_default="both",
        ),
    )
    op.add_column(
        "organizations",
        sa.Column("slug", sa.String(255), nullable=True),
    )
    op.execute(
        "UPDATE organizations SET slug = lower("
        "regexp_replace(regexp_replace(name, '[^a-zA-Z0-9\\s]', '', 'g'), '\\s+', '-', 'g'))"
    )
    op.alter_column("organizations", "slug", nullable=False)
    op.create_unique_constraint("organizations_slug_key", "organizations", ["slug"])
    op.create_index("idx_organizations_slug", "organizations", ["slug"])
    op.create_check_constraint(
        "ck_organizations_org_type",
        "organizations",
        "org_type IN ('jobs', 'admissions', 'both')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_organizations_org_type", "organizations", type_="check")
    op.drop_index("idx_organizations_slug", table_name="organizations")
    op.drop_constraint("organizations_slug_key", "organizations", type_="unique")
    op.drop_column("organizations", "slug")
    op.drop_column("organizations", "org_type")
