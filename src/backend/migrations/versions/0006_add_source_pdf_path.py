"""Add source_pdf_path column to job_vacancies for PDF ingestion.

Revision ID: 0006
Revises: 0005
"""

from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job_vacancies", sa.Column("source_pdf_path", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("job_vacancies", "source_pdf_path")
