"""Drop unused model_run_grid_subset_predictions and prediction_model_grid_subsets tables.

Revision ID: f1a2b3c4d5e6
Revises: e4a9f2c7d1b6
Create Date: 2026-08-24 00:00:00.000000

"""

import geoalchemy2
import sqlalchemy as sa
import wps_shared.db.models.common
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f1a2b3c4d5e6"
down_revision = "e4a9f2c7d1b6"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index(
        op.f("ix_model_run_grid_subset_predictions_prediction_timestamp"),
        table_name="model_run_grid_subset_predictions",
    )
    op.drop_index(
        op.f("ix_model_run_grid_subset_predictions_prediction_model_run_timestamp_id"),
        table_name="model_run_grid_subset_predictions",
    )
    op.drop_index(
        op.f("ix_model_run_grid_subset_predictions_prediction_model_grid_subset_id"),
        table_name="model_run_grid_subset_predictions",
    )
    op.drop_index(
        op.f("ix_model_run_grid_subset_predictions_id"),
        table_name="model_run_grid_subset_predictions",
    )
    op.drop_table("model_run_grid_subset_predictions")

    op.drop_index(
        op.f("ix_prediction_model_grid_subsets_prediction_model_id"),
        table_name="prediction_model_grid_subsets",
    )
    op.drop_index(
        op.f("ix_prediction_model_grid_subsets_id"), table_name="prediction_model_grid_subsets"
    )
    op.drop_index(
        "idx_prediction_model_grid_subsets_geom",
        table_name="prediction_model_grid_subsets",
        postgresql_using="gist",
    )
    op.drop_table("prediction_model_grid_subsets")


def downgrade():
    op.create_table(
        "prediction_model_grid_subsets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("prediction_model_id", sa.Integer(), nullable=False),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry(
                geometry_type="POLYGON",
                dimension=2,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
                nullable=False,
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["prediction_model_id"],
            ["prediction_models.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("prediction_model_id", "geom"),
        comment="Identify the vertices surrounding the area of interest",
    )
    op.create_index(
        "idx_prediction_model_grid_subsets_geom",
        "prediction_model_grid_subsets",
        ["geom"],
        unique=False,
        postgresql_using="gist",
    )
    op.create_index(
        op.f("ix_prediction_model_grid_subsets_id"),
        "prediction_model_grid_subsets",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_prediction_model_grid_subsets_prediction_model_id"),
        "prediction_model_grid_subsets",
        ["prediction_model_id"],
        unique=False,
    )

    op.create_table(
        "model_run_grid_subset_predictions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("prediction_model_run_timestamp_id", sa.Integer(), nullable=False),
        sa.Column("prediction_model_grid_subset_id", sa.Integer(), nullable=False),
        sa.Column(
            "prediction_timestamp", wps_shared.db.models.common.TZTimeStamp(), nullable=False
        ),
        sa.Column("tmp_tgl_2", postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column("rh_tgl_2", postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column("apcp_sfc_0", postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column("wdir_tgl_10", postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column("wind_tgl_10", postgresql.ARRAY(sa.Float()), nullable=True),
        sa.ForeignKeyConstraint(
            ["prediction_model_grid_subset_id"],
            ["prediction_model_grid_subsets.id"],
        ),
        sa.ForeignKeyConstraint(
            ["prediction_model_run_timestamp_id"],
            ["prediction_model_run_timestamps.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "prediction_model_run_timestamp_id",
            "prediction_model_grid_subset_id",
            "prediction_timestamp",
        ),
        comment="The prediction for a grid subset of a particular model run.",
    )
    op.create_index(
        op.f("ix_model_run_grid_subset_predictions_id"),
        "model_run_grid_subset_predictions",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_model_run_grid_subset_predictions_prediction_model_grid_subset_id"),
        "model_run_grid_subset_predictions",
        ["prediction_model_grid_subset_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_model_run_grid_subset_predictions_prediction_model_run_timestamp_id"),
        "model_run_grid_subset_predictions",
        ["prediction_model_run_timestamp_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_model_run_grid_subset_predictions_prediction_timestamp"),
        "model_run_grid_subset_predictions",
        ["prediction_timestamp"],
        unique=False,
    )
