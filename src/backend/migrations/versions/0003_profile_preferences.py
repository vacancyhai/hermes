"""Add profile preference columns for Phase 3.

Revision ID: 0003
Revises: 0002
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("preferred_states", JSONB, nullable=False, server_default="[]"))
    op.add_column("user_profiles", sa.Column("preferred_categories", JSONB, nullable=False, server_default="[]"))
    op.add_column("user_profiles", sa.Column("followed_organizations", JSONB, nullable=False, server_default="[]"))


def downgrade() -> None:
    op.drop_column("user_profiles", "followed_organizations")
    op.drop_column("user_profiles", "preferred_categories")
    op.drop_column("user_profiles", "preferred_states")
