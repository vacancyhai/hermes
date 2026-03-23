"""Add user_devices table and notification_delivery_log table.

user_devices: proper device registry with device_fingerprint for push
de-duplication. Replaces JSONB fcm_tokens on user_profiles.

notification_delivery_log: tracks per-channel delivery for each notification.

Revision ID: 0007
Revises: 0006
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- user_devices ---
    op.create_table(
        "user_devices",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fcm_token", sa.String(500), nullable=True),
        sa.Column("device_name", sa.String(255), nullable=False, server_default="Unknown"),
        sa.Column("device_type", sa.String(20), nullable=False, server_default="web"),
        sa.Column("device_fingerprint", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "device_type IN ('web', 'pwa', 'android', 'ios')",
            name="ck_devices_device_type",
        ),
    )
    op.create_index("idx_devices_user_id", "user_devices", ["user_id"])
    op.create_index(
        "idx_devices_fcm_token", "user_devices", ["fcm_token"],
        unique=True, postgresql_where=sa.text("fcm_token IS NOT NULL"),
    )
    op.create_index("idx_devices_fingerprint", "user_devices", ["user_id", "device_fingerprint"])

    # --- notification_delivery_log ---
    op.create_table(
        "notification_delivery_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("notification_id", UUID(as_uuid=True), sa.ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("device_id", UUID(as_uuid=True), sa.ForeignKey("user_devices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("channel IN ('in_app', 'push', 'email', 'whatsapp')", name="ck_delivery_channel"),
        sa.CheckConstraint("status IN ('pending', 'sent', 'delivered', 'failed', 'skipped')", name="ck_delivery_status"),
    )
    op.create_index("idx_delivery_notification", "notification_delivery_log", ["notification_id"])
    op.create_index("idx_delivery_user_channel", "notification_delivery_log", ["user_id", "channel"])

    # --- Migrate existing JSONB fcm_tokens → user_devices rows ---
    op.execute("""
        INSERT INTO user_devices (user_id, fcm_token, device_name, device_type, is_active, last_active_at)
        SELECT
            up.user_id,
            elem->>'token',
            COALESCE(elem->>'device_name', 'Unknown'),
            'web',
            true,
            COALESCE((elem->>'registered_at')::timestamptz, NOW())
        FROM user_profiles up,
             jsonb_array_elements(up.fcm_tokens) AS elem
        WHERE jsonb_array_length(up.fcm_tokens) > 0
        ON CONFLICT DO NOTHING
    """)


def downgrade() -> None:
    op.drop_table("notification_delivery_log")
    op.drop_table("user_devices")
