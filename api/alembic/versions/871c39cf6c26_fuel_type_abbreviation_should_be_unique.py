"""Fuel type abbreviation should be unique

Revision ID: 871c39cf6c26
Revises: af108f346073
Create Date: 2022-02-01 13:53:33.761953

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '871c39cf6c26'
down_revision = 'af108f346073'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(op.f('ix_fuel_types_abbrev'), 'fuel_types', ['abbrev'], unique=True)
    op.create_unique_constraint(None, 'planning_weather_stations', ['station_code', 'planning_area_id'])


def downgrade():
    op.drop_constraint(None, 'planning_weather_stations', type_='unique')
    op.drop_index(op.f('ix_fuel_types_abbrev'), table_name='fuel_types')
