"""Remove redundant constraint

Revision ID: af108f346073
Revises: 274bec360d8c
Create Date: 2022-01-31 11:28:46.590311

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'af108f346073'
down_revision = '274bec360d8c'
branch_labels = None
depends_on = None


def upgrade():
    # ### Prod still has this constraint in the DB and is running alembic version 274bec360d8c ###
    op.execute('ALTER TABLE planning_weather_stations DROP CONSTRAINT IF EXISTS planning_weather_stations_station_code_key')


def downgrade():
    op.create_unique_constraint('planning_weather_stations_station_code_key',
                                'planning_weather_stations', ['station_code'])
