"""Add missing created_at/updated_at columns to organizations, notifications, user_profiles, user_devices.

Revision ID: 0002_add_missing_timestamps
Revises: 0001_initial
Create Date: 2026-04-20
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_add_missing_timestamps"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # organizations — add updated_at
    op.add_column(
        "organizations",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # notifications — add updated_at
    op.add_column(
        "notifications",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # user_profiles — add created_at
    op.add_column(
        "user_profiles",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # user_devices — add updated_at
    op.add_column(
        "user_devices",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_column("user_devices", "updated_at")
    op.drop_column("user_profiles", "created_at")
    op.drop_column("notifications", "updated_at")
    op.drop_column("organizations", "updated_at")
