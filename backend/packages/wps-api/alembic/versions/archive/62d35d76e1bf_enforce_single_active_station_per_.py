"""Enforce single active station per planning area

Revision ID: 62d35d76e1bf
Revises: 6d29ebbf61f7
Create Date: 2022-08-02 11:29:50.848643

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '62d35d76e1bf'
down_revision = '6d29ebbf61f7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('unique_non_deleted_station_per_planning_area', 'planning_weather_stations', [
                    'is_deleted', 'station_code', 'planning_area_id'], unique=True, postgresql_where='not is_deleted')


def downgrade():
    op.drop_index('unique_non_deleted_station_per_planning_area',
                  table_name='planning_weather_stations', postgresql_where='not is_deleted')
