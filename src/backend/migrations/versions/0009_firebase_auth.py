"""Add firebase_uid and migration_status to users table for Firebase Auth.

Makes password_hash nullable since Firebase-only users won't have one.

Revision ID: 0009
Revises: 0008
Create Date: 2026-03-23
"""

from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("firebase_uid", sa.String(128), nullable=True),
    )
    op.create_index("ix_users_firebase_uid", "users", ["firebase_uid"], unique=True)
    op.alter_column("users", "password_hash", nullable=True)
    op.add_column(
        "users",
        sa.Column(
            "migration_status",
            sa.String(20),
            nullable=False,
            server_default="legacy",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "migration_status")
    op.alter_column("users", "password_hash", nullable=False)
    op.drop_index("ix_users_firebase_uid", table_name="users")
    op.drop_column("users", "firebase_uid")
