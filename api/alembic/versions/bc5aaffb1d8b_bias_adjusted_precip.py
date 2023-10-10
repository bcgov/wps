"""Bias adjusted precip

Revision ID: bc5aaffb1d8b
Revises: f49418d95584
Create Date: 2023-09-12 10:59:44.691128

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bc5aaffb1d8b'
down_revision = 'f49418d95584'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('weather_station_model_predictions', sa.Column('bias_adjusted_apcp_sfc_0', sa.Float(), nullable=True))
    op.add_column('weather_station_model_predictions', sa.Column('bias_adjusted_precip_24h', sa.Float(), nullable=True))
    op.execute("DROP MATERIALIZED VIEW morecast_2_materialized_view;")
    op.execute("""
               CREATE MATERIALIZED VIEW morecast_2_materialized_view AS
            SELECT weather_station_model_predictions.prediction_timestamp, prediction_models.abbreviation, weather_station_model_predictions.station_code,
                weather_station_model_predictions.rh_tgl_2, weather_station_model_predictions.tmp_tgl_2, weather_station_model_predictions.bias_adjusted_temperature,
                weather_station_model_predictions.bias_adjusted_rh, weather_station_model_predictions.precip_24h, weather_station_model_predictions.wdir_tgl_10,
                weather_station_model_predictions.wind_tgl_10, weather_station_model_predictions.bias_adjusted_wind_speed, weather_station_model_predictions.bias_adjusted_wdir,
                weather_station_model_predictions.bias_adjusted_apcp_sfc_0, weather_station_model_predictions.bias_adjusted_precip_24h, weather_station_model_predictions.update_date,
                weather_station_model_predictions.prediction_model_run_timestamp_id
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


def downgrade():
    # Drop materialized view before dropping columns as the columns cannot be dropped because the existing materialized view depends on them.
    op.execute("DROP MATERIALIZED VIEW morecast_2_materialized_view;")
    op.drop_column('weather_station_model_predictions', 'bias_adjusted_precip_24h')
    op.drop_column('weather_station_model_predictions', 'bias_adjusted_apcp_sfc_0')
    op.execute("""
               CREATE MATERIALIZED VIEW morecast_2_materialized_view AS
            SELECT weather_station_model_predictions.prediction_timestamp, prediction_models.abbreviation, weather_station_model_predictions.station_code, 
                weather_station_model_predictions.rh_tgl_2, weather_station_model_predictions.tmp_tgl_2, weather_station_model_predictions.bias_adjusted_temperature,
                weather_station_model_predictions.bias_adjusted_rh, weather_station_model_predictions.precip_24h, weather_station_model_predictions.wdir_tgl_10, 
                weather_station_model_predictions.wind_tgl_10, weather_station_model_predictions.bias_adjusted_wind_speed, weather_station_model_predictions.bias_adjusted_wdir,
                weather_station_model_predictions.update_date
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
