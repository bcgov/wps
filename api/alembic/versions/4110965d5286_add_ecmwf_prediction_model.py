"""add ecmwf prediction model

Revision ID: 4110965d5286
Revises: 4014ddf1f874
Create Date: 2025-01-15 15:42:13.384776

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "4110965d5286"
down_revision = "4014ddf1f874"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        'INSERT INTO prediction_models(name, abbreviation, projection)\
        VALUES(\'ECMWF Integrated Forecast System\', \'ECMWF\', \'latlon.0.25deg\')'
    )


def downgrade():
    op.execute('DELETE FROM prediction_models WHERE abbreviation = \'ECMWF\'')
