"""Add user_job_eligibility and user_admission_eligibility tables.

Revision ID: 0002_user_eligibility_tables
Revises: 0001_initial
Create Date: 2026-04-20
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_user_eligibility_tables"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_eligibility",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column(
            "reasons",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("user_id", "job_id", name="uq_job_elig_user_job"),
    )
    op.create_index("ix_job_elig_user_id", "job_eligibility", ["user_id"])
    op.create_index("ix_job_elig_job_id", "job_eligibility", ["job_id"])

    op.create_table(
        "admission_eligibility",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "admission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column(
            "reasons",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("user_id", "admission_id", name="uq_adm_elig_user_admission"),
    )
    op.create_index("ix_adm_elig_user_id", "admission_eligibility", ["user_id"])
    op.create_index("ix_adm_elig_admission_id", "admission_eligibility", ["admission_id"])


def downgrade() -> None:
    op.drop_table("admission_eligibility")
    op.drop_table("job_eligibility")
