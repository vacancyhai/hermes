"""Add application fee columns to job_vacancies for Phase 6.

Revision ID: 0005
Revises: 0004
"""

from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job_vacancies", sa.Column("fee_general", sa.Integer(), nullable=True))
    op.add_column("job_vacancies", sa.Column("fee_obc", sa.Integer(), nullable=True))
    op.add_column("job_vacancies", sa.Column("fee_sc_st", sa.Integer(), nullable=True))
    op.add_column("job_vacancies", sa.Column("fee_ews", sa.Integer(), nullable=True))
    op.add_column("job_vacancies", sa.Column("fee_female", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("job_vacancies", "fee_female")
    op.drop_column("job_vacancies", "fee_ews")
    op.drop_column("job_vacancies", "fee_sc_st")
    op.drop_column("job_vacancies", "fee_obc")
    op.drop_column("job_vacancies", "fee_general")
