"""Update status check constraints for jobs and admissions.

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-15
"""

from alembic import op

revision = "0002"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Jobs: replace cancelled with inactive ──────────────────────────────
    op.execute("ALTER TABLE jobs DROP CONSTRAINT IF EXISTS ck_jobs_status")
    op.execute(
        "ALTER TABLE jobs ADD CONSTRAINT ck_jobs_status "
        "CHECK (status IN ('upcoming', 'active', 'inactive', 'closed'))"
    )
    # Migrate any existing cancelled rows to closed
    op.execute("UPDATE jobs SET status = 'closed' WHERE status = 'cancelled'")

    # ── Admissions: replace completed/cancelled with inactive/closed ───────
    op.execute("ALTER TABLE admissions DROP CONSTRAINT IF EXISTS ck_admission_status")
    op.execute(
        "ALTER TABLE admissions ADD CONSTRAINT ck_admission_status "
        "CHECK (status IN ('upcoming', 'active', 'inactive', 'closed'))"
    )
    # Migrate any existing completed/cancelled rows to closed
    op.execute(
        "UPDATE admissions SET status = 'closed' "
        "WHERE status IN ('completed', 'cancelled')"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE jobs DROP CONSTRAINT IF EXISTS ck_jobs_status")
    op.execute(
        "ALTER TABLE jobs ADD CONSTRAINT ck_jobs_status "
        "CHECK (status IN ('upcoming', 'active', 'closed', 'cancelled'))"
    )

    op.execute("ALTER TABLE admissions DROP CONSTRAINT IF EXISTS ck_admission_status")
    op.execute(
        "ALTER TABLE admissions ADD CONSTRAINT ck_admission_status "
        "CHECK (status IN ('upcoming', 'active', 'completed', 'cancelled'))"
    )
