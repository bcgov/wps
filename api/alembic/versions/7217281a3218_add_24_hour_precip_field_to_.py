"""Add 24 hour precip field to WeatherStationModelPrediction

Revision ID: 7217281a3218
Revises: 4916cd5313de
Create Date: 2023-07-25 10:53:19.447483

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7217281a3218'
down_revision = '4916cd5313de'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('weather_station_model_predictions', sa.Column('precip_24h', sa.Float(), nullable=True))

    op.execute("""CREATE MATERIALIZED VIEW morecast_2_materialized_view_precip AS 
            SELECT weather_station_model_predictions.prediction_timestamp, prediction_models.abbreviation, weather_station_model_predictions.station_code, weather_station_model_predictions.rh_tgl_2, weather_station_model_predictions.tmp_tgl_2, weather_station_model_predictions.bias_adjusted_temperature, weather_station_model_predictions.bias_adjusted_rh, weather_station_model_predictions.precip_24h, weather_station_model_predictions.wdir_tgl_10, weather_station_model_predictions.wind_tgl_10, weather_station_model_predictions.update_date 
            FROM weather_station_model_predictions 
            JOIN prediction_model_run_timestamps 
            ON weather_station_model_predictions.prediction_model_run_timestamp_id = prediction_model_run_timestamps.id JOIN prediction_models 
            ON prediction_model_run_timestamps.prediction_model_id = prediction_models.id 
            JOIN ( 
            SELECT max(weather_station_model_predictions.prediction_timestamp) AS latest_prediction, weather_station_model_predictions.station_code AS station_code, 
            date(weather_station_model_predictions.prediction_timestamp) AS unique_day 
            FROM weather_station_model_predictions 
            WHERE date_part('hour', weather_station_model_predictions.prediction_timestamp) = 20 
            GROUP BY weather_station_model_predictions.station_code, date(weather_station_model_predictions.prediction_timestamp) 
            ) AS latest 
            ON weather_station_model_predictions.prediction_timestamp = latest.latest_prediction AND weather_station_model_predictions.station_code = latest.station_code 
            ORDER BY weather_station_model_predictions.update_date DESC;""")

    op.create_index(op.f('ix_mat_view_precip_prediction_timestamp'),
                    'morecast_2_materialized_view_precip', ['prediction_timestamp'], unique=False)
    op.create_index(op.f('ix_mat_view_precip_station_code'),
                    'morecast_2_materialized_view_precip', ['station_code'], unique=False)


def downgrade():
    op.drop_column('weather_station_model_predictions', 'precip_24h')
    op.drop_index(op.f('ix_mat_view_precip_prediction_timestamp'), table_name='morecast_2_materialized_view_precip')
    op.drop_index(op.f('ix_mat_view_precip_station_code'), table_name='morecast_2_materialized_view_precip')
    op.execute('DROP MATERIALIZED VIEW morecast_2_materialized_view_precip')
