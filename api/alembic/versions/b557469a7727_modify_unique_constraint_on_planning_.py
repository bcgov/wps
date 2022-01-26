"""Modify unique constraint on planning_weather_stations

Revision ID: b557469a7727
Revises: d99fcdc4800d
Create Date: 2022-01-17 10:15:33.448252

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b557469a7727'
down_revision = 'd99fcdc4800d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint('unique_station_code_for_planning_area',
                                'planning_weather_stations', ['station_code', 'planning_area_id'])


def downgrade():
    op.drop_constraint('unique_station_code_for_planning_area', 'planning_weather_stations', type_='unique')
