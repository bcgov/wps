"""Add HRDPS rotated latlon prediction model

Revision ID: a4fb7e8a1d2c
Revises: d3513840fd37
Create Date: 2026-06-03 00:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "a4fb7e8a1d2c"
down_revision = "d3513840fd37"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "SELECT setval(pg_get_serial_sequence('prediction_models', 'id'), MAX(id)) FROM prediction_models"
    )
    op.execute(
        """
        INSERT INTO prediction_models (abbreviation, name, projection)
        VALUES ('HRDPS', 'High Resolution Deterministic Prediction System', 'RLatLon0.0225')
        ON CONFLICT (abbreviation, projection) DO NOTHING
        """
    )


def downgrade():
    op.execute(
        "DELETE FROM prediction_models WHERE abbreviation = 'HRDPS' AND projection = 'RLatLon0.0225'"
    )
