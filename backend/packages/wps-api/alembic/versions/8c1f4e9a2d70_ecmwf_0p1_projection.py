"""Add ECMWF 0.1 degree prediction model.

Revision ID: 8c1f4e9a2d70
Revises: b7e3c1d9a4f2
Create Date: 2026-11-12 00:00:00.000000
"""

from alembic import op

revision = "8c1f4e9a2d70"
down_revision = "b7e3c1d9a4f2"
branch_labels = None
depends_on = None


def upgrade():
    # seeded model IDs do not advance the sequence
    op.execute(
        "SELECT setval(pg_get_serial_sequence('prediction_models', 'id'), MAX(id)) "
        "FROM prediction_models"
    )
    op.execute(
        """
        INSERT INTO prediction_models (abbreviation, name, projection)
        VALUES ('ECMWF', 'ECMWF Integrated Forecast System', 'latlon.0.1deg')
        ON CONFLICT (abbreviation, projection) DO NOTHING
        """
    )


def downgrade():
    model_ids = (
        "SELECT id FROM prediction_models "
        "WHERE abbreviation = 'ECMWF' AND projection = 'latlon.0.1deg'"
    )
    run_ids = (
        f"SELECT id FROM prediction_model_run_timestamps WHERE prediction_model_id IN ({model_ids})"
    )
    # remove dependent data before deleting this resolution's runs and model
    for table in (
        "fire_watch_weather",
        "weather_station_model_predictions",
        "model_run_predictions",
    ):
        op.execute(f"DELETE FROM {table} WHERE prediction_model_run_timestamp_id IN ({run_ids})")
    op.execute(f"DELETE FROM model_run_for_sfms WHERE prediction_model_id IN ({model_ids})")
    op.execute(
        f"DELETE FROM prediction_model_run_timestamps WHERE prediction_model_id IN ({model_ids})"
    )
    op.execute(f"DELETE FROM prediction_models WHERE id IN ({model_ids})")
    # clear markers so a later upgrade can process these forecasts again
    op.execute("DELETE FROM processed_model_run_urls WHERE url LIKE '%/ifs/0p1/%'")
