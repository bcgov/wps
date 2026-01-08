"""wfwx_update_date part of unique constraint

Revision ID: 39806f02cdec
Revises: b557469a7727
Create Date: 2021-12-14 11:38:35.435805

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '39806f02cdec'
down_revision = 'b557469a7727'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('noon_forecasts_weather_date_station_code_temp_valid_tempera_key',
                       'noon_forecasts', type_='unique')
    op.create_unique_constraint('unique_forecast', 'noon_forecasts', [
                                'weather_date', 'wfwx_update_date', 'station_code'])
    op.drop_column('noon_forecasts', 'danger_rating',
                   existing_type=sa.INTEGER(),
                   nullable=True)


def downgrade():
    op.add_column('noon_forecasts',
                  sa.Column('danger_rating',
                            sa.INTEGER(),
                            nullable=True))
    op.drop_constraint('unique_forecast', 'noon_forecasts', type_='unique')
    op.create_unique_constraint('noon_forecasts_weather_date_station_code_temp_valid_tempera_key', 'noon_forecasts', [
                                'weather_date', 'station_code', 'temp_valid', 'temperature', 'rh_valid', 'relative_humidity', 'wdir_valid', 'wind_direction', 'wspeed_valid', 'wind_speed', 'precip_valid', 'precipitation', 'gc', 'ffmc', 'dmc', 'dc', 'isi', 'bui', 'fwi', 'danger_rating'])
