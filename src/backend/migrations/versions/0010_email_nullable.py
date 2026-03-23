"""Make users.email nullable to support phone-only Firebase users.

Revision ID: 0010
Revises: 0009
Create Date: 2026-03-23
"""

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("users", "email", nullable=True)


def downgrade() -> None:
    # NOTE: rows without email must be back-filled before downgrading
    op.alter_column("users", "email", nullable=False)
