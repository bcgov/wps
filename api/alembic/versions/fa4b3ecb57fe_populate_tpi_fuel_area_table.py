"""Populate tpi_fuel_area table

Revision ID: fa4b3ecb57fe
Revises: 1e6932096921
Create Date: 2025-01-21 10:04:48.838953

"""

from app.auto_spatial_advisory.process_tpi_fuel_area import process_tpi_fuel_area


# revision identifiers, used by Alembic.
revision = "fa4b3ecb57fe"
down_revision = "1e6932096921"
branch_labels = None
depends_on = None


def upgrade():
    process_tpi_fuel_area()
    pass


def downgrade():
    pass
