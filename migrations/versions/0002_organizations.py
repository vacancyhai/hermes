"""Add organizations table, jobs.organization_id FK, extend user_tracks entity_type.

Revision ID: 0002_organizations
Revises: 0001_initial
Create Date: 2026-04-19
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_organizations"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. organizations table ─────────────────────────────────────────────────
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("short_name", sa.String(50), nullable=True),
        sa.Column("logo_url", sa.Text(), nullable=True),
        sa.Column("website_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_organizations_slug", "organizations", ["slug"])
    op.create_index("idx_organizations_name", "organizations", ["name"])

    # ── 2. jobs.organization_id FK (soft — VARCHAR organization column kept) ───
    op.add_column(
        "jobs",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("idx_jobs_organization_id", "jobs", ["organization_id"])

    # ── 3. user_tracks: extend entity_type VARCHAR and CHECK ──────────────────
    op.alter_column("user_tracks", "entity_type", type_=sa.String(12), existing_type=sa.String(10), nullable=False)
    op.execute("ALTER TABLE user_tracks DROP CONSTRAINT ck_user_tracks_entity_type")
    op.execute(
        "ALTER TABLE user_tracks ADD CONSTRAINT ck_user_tracks_entity_type "
        "CHECK (entity_type IN ('job', 'admission', 'organization'))"
    )

    # ── 4. Backfill organizations from existing jobs (unique org names) ────────
    op.execute("""
        INSERT INTO organizations (name, slug)
        SELECT DISTINCT
            organization,
            lower(regexp_replace(
                regexp_replace(organization, '[^a-zA-Z0-9\\s]', '', 'g'),
                '\\s+', '-', 'g'
            ))
        FROM jobs
        WHERE organization IS NOT NULL AND organization != ''
        ON CONFLICT (name) DO NOTHING
    """)

    # ── 5. Backfill jobs.organization_id from the newly inserted orgs ─────────
    op.execute("""
        UPDATE jobs j
        SET organization_id = o.id
        FROM organizations o
        WHERE j.organization = o.name
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE user_tracks DROP CONSTRAINT ck_user_tracks_entity_type")
    op.execute(
        "ALTER TABLE user_tracks ADD CONSTRAINT ck_user_tracks_entity_type "
        "CHECK (entity_type IN ('job', 'admission'))"
    )
    op.drop_index("idx_jobs_organization_id", table_name="jobs")
    op.drop_column("jobs", "organization_id")
    op.drop_index("idx_organizations_name", table_name="organizations")
    op.drop_index("idx_organizations_slug", table_name="organizations")
    op.drop_table("organizations")
