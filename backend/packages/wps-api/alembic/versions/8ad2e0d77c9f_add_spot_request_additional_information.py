"""Add spot request additional information

Revision ID: 8ad2e0d77c9f
Revises: f5bb9e85fd0a
Create Date: 2026-05-19 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8ad2e0d77c9f"
down_revision = "f5bb9e85fd0a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("spot_request", sa.Column("additional_information", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("spot_request", "additional_information")
