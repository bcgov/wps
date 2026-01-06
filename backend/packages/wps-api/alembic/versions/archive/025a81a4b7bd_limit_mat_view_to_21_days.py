"""limit mat view to 21 days

Revision ID: 025a81a4b7bd
Revises: d392e4a5a499
Create Date: 2024-05-24 16:06:53.822488

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '025a81a4b7bd'
down_revision = 'd392e4a5a499'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
    op.f('ix_wsm_prediction_timestamp_station_code'),
    'weather_station_model_predictions',
    ['prediction_timestamp', 'station_code'],
    unique=False
)

    # drop mat view and limit the number of rows by prediction_timestamp within the last 21 days
    op.execute("DROP MATERIALIZED VIEW morecast_2_materialized_view;")
    op.execute("""
    CREATE MATERIALIZED VIEW morecast_2_materialized_view AS
    SELECT
	weather_station_model_predictions.prediction_timestamp,
	prediction_models.abbreviation,
	weather_station_model_predictions.station_code,
	weather_station_model_predictions.rh_tgl_2,
	weather_station_model_predictions.tmp_tgl_2,
	weather_station_model_predictions.bias_adjusted_temperature,
	weather_station_model_predictions.bias_adjusted_rh,
	weather_station_model_predictions.precip_24h,
	weather_station_model_predictions.wdir_tgl_10,
	weather_station_model_predictions.wind_tgl_10,
	weather_station_model_predictions.bias_adjusted_wind_speed,
	weather_station_model_predictions.bias_adjusted_wdir,
	weather_station_model_predictions.bias_adjusted_precip_24h,
	weather_station_model_predictions.update_date,
	weather_station_model_predictions.prediction_model_run_timestamp_id
    FROM
        weather_station_model_predictions
    JOIN prediction_model_run_timestamps
                ON
        weather_station_model_predictions.prediction_model_run_timestamp_id = prediction_model_run_timestamps.id
    JOIN prediction_models
                ON
        prediction_model_run_timestamps.prediction_model_id = prediction_models.id
    JOIN (
        SELECT
            max(weather_station_model_predictions.prediction_timestamp) AS latest_prediction,
            weather_station_model_predictions.station_code AS station_code,
            date(weather_station_model_predictions.prediction_timestamp) AS unique_day
        FROM
            weather_station_model_predictions
        WHERE
            date_part('hour',
            weather_station_model_predictions.prediction_timestamp) = 20
        GROUP BY
            weather_station_model_predictions.station_code,
            date(weather_station_model_predictions.prediction_timestamp)
                ) AS latest
                ON
        weather_station_model_predictions.prediction_timestamp = latest.latest_prediction
        AND weather_station_model_predictions.station_code = latest.station_code
    WHERE
        weather_station_model_predictions.prediction_timestamp >= current_date - INTERVAL '21 days'
    ORDER BY
        weather_station_model_predictions.update_date DESC;
    """)
    

def downgrade():
    op.drop_index('ix_wsm_prediction_timestamp_station_code', if_exists=True)
    op.execute("DROP MATERIALIZED VIEW morecast_2_materialized_view;")
    op.execute("""
        CREATE MATERIALIZED VIEW morecast_2_materialized_view AS
        SELECT weather_station_model_predictions.prediction_timestamp, prediction_models.abbreviation, weather_station_model_predictions.station_code,
            weather_station_model_predictions.rh_tgl_2, weather_station_model_predictions.tmp_tgl_2, weather_station_model_predictions.bias_adjusted_temperature,
            weather_station_model_predictions.bias_adjusted_rh, weather_station_model_predictions.precip_24h, weather_station_model_predictions.wdir_tgl_10,
            weather_station_model_predictions.wind_tgl_10, weather_station_model_predictions.bias_adjusted_wind_speed, weather_station_model_predictions.bias_adjusted_wdir,
            weather_station_model_predictions.bias_adjusted_precip_24h, weather_station_model_predictions.update_date,
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
