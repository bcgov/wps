"""add ecmwf model

Revision ID: 42a9dae10dca
Revises: 6a31639810b0
Create Date: 2025-04-28 14:45:11.701108

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "42a9dae10dca"
down_revision = "6a31639810b0"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "INSERT INTO prediction_models(name, abbreviation, projection)\
        VALUES('ECMWF Integrated Forecast System', 'ECMWF', 'latlon.0.25deg')"
    )


def downgrade():
    op.execute("DELETE FROM prediction_models WHERE abbreviation = 'ECMWF'")
