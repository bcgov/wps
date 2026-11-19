"""Store model elevations for Morecast stations."""

import sqlalchemy as sa
from alembic import op

revision = "c7f32a981de4"
down_revision = "8c1f4e9a2d70"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "model_run_station_elevations",
        sa.Column(
            "prediction_model_run_timestamp_id",
            sa.Integer(),
            sa.ForeignKey("prediction_model_run_timestamps.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("station_code", sa.Integer(), primary_key=True),
        sa.Column("elevation", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("model_run_station_elevations")
