"""Key fire watch weather on the model run's time instead of its prediction_model_run_timestamps id.

Model runs are no longer recorded in Postgres: they are in the `runs` table in object storage,
identified by model and run time. Fire watch only uses ECMWF, so the run time alone identifies
the run.

Revision ID: 3d7e5b1a9c42
Revises: 8c1f4e9a2d70
Create Date: 2026-11-17 00:00:00.000000

"""

import sqlalchemy as sa
import wps_shared.db.models.common
from alembic import op

# revision identifiers, used by Alembic.
revision = "3d7e5b1a9c42"
down_revision = "8c1f4e9a2d70"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "fire_watch_weather",
        sa.Column(
            "prediction_run_timestamp",
            wps_shared.db.models.common.TZTimeStamp(),
            nullable=True,
        ),
    )
    op.execute(
        """
        UPDATE fire_watch_weather AS weather
        SET prediction_run_timestamp = run.prediction_run_timestamp
        FROM prediction_model_run_timestamps AS run
        WHERE run.id = weather.prediction_model_run_timestamp_id
        """
    )
    op.alter_column("fire_watch_weather", "prediction_run_timestamp", nullable=False)
    op.create_index(
        op.f("ix_fire_watch_weather_prediction_run_timestamp"),
        "fire_watch_weather",
        ["prediction_run_timestamp"],
        unique=False,
    )
    # Dropping the column drops its foreign key and index too.
    op.drop_column("fire_watch_weather", "prediction_model_run_timestamp_id")


def downgrade():
    op.add_column(
        "fire_watch_weather",
        sa.Column("prediction_model_run_timestamp_id", sa.Integer(), nullable=True),
    )
    # Fire watch weather comes from ECMWF. Where both grids have a run at that time, take the
    # 0.1 degree one, as fire watch did.
    op.execute(
        """
        UPDATE fire_watch_weather AS weather
        SET prediction_model_run_timestamp_id = (
            SELECT run.id
            FROM prediction_model_run_timestamps AS run
            JOIN prediction_models AS model ON model.id = run.prediction_model_id
            WHERE model.abbreviation = 'ECMWF'
            AND run.prediction_run_timestamp = weather.prediction_run_timestamp
            ORDER BY (model.projection = 'latlon.0.1deg') DESC
            LIMIT 1
        )
        """
    )
    # Weather for a run that was never recorded in Postgres cannot be kept. The fire watch job
    # calculates it again.
    op.execute("DELETE FROM fire_watch_weather WHERE prediction_model_run_timestamp_id IS NULL")
    op.alter_column("fire_watch_weather", "prediction_model_run_timestamp_id", nullable=False)
    op.create_foreign_key(
        None,
        "fire_watch_weather",
        "prediction_model_run_timestamps",
        ["prediction_model_run_timestamp_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_fire_watch_weather_prediction_model_run_timestamp_id"),
        "fire_watch_weather",
        ["prediction_model_run_timestamp_id"],
        unique=False,
    )
    op.drop_index(
        op.f("ix_fire_watch_weather_prediction_run_timestamp"), table_name="fire_watch_weather"
    )
    op.drop_column("fire_watch_weather", "prediction_run_timestamp")
