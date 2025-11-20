"""Fuel type abbreviation should be unique

Revision ID: 871c39cf6c26
Revises: af108f346073
Create Date: 2022-02-01 13:53:33.761953

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '871c39cf6c26'
down_revision = 'af108f346073'
branch_labels = None
depends_on = None


def upgrade():
    # make fuel type abbreviation index, and unique.
    op.create_index(op.f('ix_fuel_types_abbrev'), 'fuel_types', ['abbrev'], unique=True)
    # something extremely weird happened - our production environment doesn't have this index, but
    # our locals do! So for local to remain consisted, we drop the constraint if it exists
    op.execute("ALTER TABLE planning_weather_stations DROP CONSTRAINT IF EXISTS unique_station_code_for_planning_area")
    op.create_unique_constraint('unique_station_code_for_planning_area',
                                'planning_weather_stations', ['station_code', 'planning_area_id'])


def downgrade():
    # drop index and unique constraint.
    op.drop_constraint('unique_station_code_for_planning_area',
                       'planning_weather_stations', type_='unique')
    op.drop_index(op.f('ix_fuel_types_abbrev'), table_name='fuel_types')
