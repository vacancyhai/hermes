"""Add fcm_tokens column to user_profiles for Phase 5.

Revision ID: 0004
Revises: 0003
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("fcm_tokens", JSONB, nullable=False, server_default="[]"))


def downgrade() -> None:
    op.drop_column("user_profiles", "fcm_tokens")
