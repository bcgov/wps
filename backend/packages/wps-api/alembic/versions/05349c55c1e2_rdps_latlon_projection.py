"""rdps_latlon_projection

Revision ID: 05349c55c1e2
Revises: 591bf3e24705
Create Date: 2026-04-14 16:16:51.902177

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '05349c55c1e2'
down_revision = '591bf3e24705'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "INSERT INTO prediction_models (abbreviation, name, projection) "
        "VALUES ('RDPS', 'Regional Deterministic Prediction System', 'RLatLon0.09')"
    )


def downgrade():
    op.execute(
        "DELETE FROM prediction_models WHERE abbreviation = 'RDPS' AND projection = 'RLatLon0.09'"
    )
