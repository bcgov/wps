"""add ecmwf model

Revision ID: 77a9198917be
Revises: 2b3755392ad8
Create Date: 2024-04-02 16:47:02.051864

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '77a9198917be'
down_revision = '2b3755392ad8'
branch_labels = None
depends_on = None


def upgrade():
    """ Insert ECMWF model data into prediction_models table """
    op.execute(
        'INSERT INTO prediction_models (abbreviation, name, projection) VALUES (\'ECMWF\', \'European Centre for Medium-Range Weather Forecasts\', \'lonlat.0.25deg\')')


def downgrade():
    """ Delete the ECMWF model from prediction_models """
    op.execute('DELETE from prediction_models WHERE name = \'ECMWF\'')
