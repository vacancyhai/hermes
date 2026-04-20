"""Consolidate fee_general/obc/sc_st/ews/female into single fee JSONB column.

Revision ID: 0003_fee_jsonb
Revises: 0002_add_missing_timestamps
Create Date: 2026-04-20
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0003_fee_jsonb"
down_revision = "0002_add_missing_timestamps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("jobs", "admissions"):
        # 1. Add fee JSONB column
        op.add_column(
            table,
            sa.Column(
                "fee",
                JSONB,
                nullable=False,
                server_default="{}",
            ),
        )

        # 2. Backfill from existing columns
        op.execute(
            f"""
            UPDATE {table} SET fee = (
                SELECT jsonb_strip_nulls(jsonb_build_object(
                    'general', fee_general,
                    'obc',     fee_obc,
                    'sc_st',   fee_sc_st,
                    'ews',     fee_ews,
                    'female',  fee_female
                ))
            )
            WHERE fee_general IS NOT NULL
               OR fee_obc     IS NOT NULL
               OR fee_sc_st   IS NOT NULL
               OR fee_ews     IS NOT NULL
               OR fee_female  IS NOT NULL
            """
        )

        # 3. Drop old columns
        op.drop_column(table, "fee_general")
        op.drop_column(table, "fee_obc")
        op.drop_column(table, "fee_sc_st")
        op.drop_column(table, "fee_ews")
        op.drop_column(table, "fee_female")


def downgrade() -> None:
    for table in ("jobs", "admissions"):
        op.add_column(table, sa.Column("fee_general", sa.Integer(), nullable=True))
        op.add_column(table, sa.Column("fee_obc", sa.Integer(), nullable=True))
        op.add_column(table, sa.Column("fee_sc_st", sa.Integer(), nullable=True))
        op.add_column(table, sa.Column("fee_ews", sa.Integer(), nullable=True))
        op.add_column(table, sa.Column("fee_female", sa.Integer(), nullable=True))

        op.execute(
            f"""
            UPDATE {table} SET
                fee_general = (fee->>'general')::int,
                fee_obc     = (fee->>'obc')::int,
                fee_sc_st   = (fee->>'sc_st')::int,
                fee_ews     = (fee->>'ews')::int,
                fee_female  = (fee->>'female')::int
            WHERE fee != '{{}}'
            """
        )

        op.drop_column(table, "fee")
