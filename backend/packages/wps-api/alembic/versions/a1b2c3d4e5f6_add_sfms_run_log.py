"""add sfms_run_log

Revision ID: a1b2c3d4e5f6
Revises: cf8397b26783
Create Date: 2026-01-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "cf8397b26783"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sfms_run_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("job_name", sa.String(), nullable=False, index=True),
        sa.Column("target_date", sa.Date(), nullable=False, index=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
    )


def downgrade():
    op.drop_table("sfms_run_log")

