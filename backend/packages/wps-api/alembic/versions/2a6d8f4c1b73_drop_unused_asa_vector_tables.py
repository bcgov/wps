"""Drop unused auto spatial advisory vector tables.

Revision ID: 2a6d8f4c1b73
Revises: f1a2b3c4d5e6
Create Date: 2026-09-24 10:08:39.201412

"""

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from wps_shared.db.models.common import TZTimeStamp

# revision identifiers, used by Alembic.
revision = "2a6d8f4c1b73"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DELETE FROM application_data_tables WHERE table_name = 'advisory_fuel_types'")

    op.drop_index(
        op.f("ix_advisory_elevation_stats_run_parameters"),
        table_name="advisory_elevation_stats",
    )
    op.drop_index(op.f("ix_advisory_elevation_stats_id"), table_name="advisory_elevation_stats")
    op.drop_index(
        op.f("ix_advisory_elevation_stats_advisory_shape_id"),
        table_name="advisory_elevation_stats",
    )
    op.drop_table("advisory_elevation_stats")

    op.drop_index(op.f("ix_advisory_fuel_types_id"), table_name="advisory_fuel_types")
    op.drop_index(
        op.f("ix_advisory_fuel_types_fuel_type_raster_id"),
        table_name="advisory_fuel_types",
    )
    op.drop_index(op.f("ix_advisory_fuel_types_fuel_type_id"), table_name="advisory_fuel_types")
    op.drop_index(
        "idx_advisory_fuel_types_geom",
        table_name="advisory_fuel_types",
        postgresql_using="gist",
    )
    op.drop_table("advisory_fuel_types")

    op.drop_index(
        op.f("ix_advisory_classified_hfi_threshold"),
        table_name="advisory_classified_hfi",
    )
    op.drop_index(
        op.f("ix_advisory_classified_hfi_run_type"),
        table_name="advisory_classified_hfi",
    )
    op.drop_index(op.f("ix_advisory_classified_hfi_id"), table_name="advisory_classified_hfi")
    op.drop_index(
        "idx_advisory_classified_hfi_geom",
        table_name="advisory_classified_hfi",
        postgresql_using="gist",
    )
    op.drop_table("advisory_classified_hfi")


def downgrade():
    # the schemas are restored, but rows removed by the upgrade cannot be recovered
    op.create_table(
        "advisory_classified_hfi",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("threshold", sa.Integer(), nullable=False),
        sa.Column(
            "run_type",
            postgresql.ENUM("forecast", "actual", name="runtypeenum", create_type=False),
            nullable=False,
        ),
        sa.Column("run_datetime", TZTimeStamp(), nullable=False),
        sa.Column("for_date", sa.Date(), nullable=False),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry(
                geometry_type="POLYGON",
                srid=3005,
                dimension=2,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["threshold"],
            ["advisory_hfi_classification_threshold.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        comment="HFI classification for some forecast/advisory run on some day, for some date",
    )
    op.create_index(
        "idx_advisory_classified_hfi_geom",
        "advisory_classified_hfi",
        ["geom"],
        unique=False,
        postgresql_using="gist",
    )
    op.create_index(
        op.f("ix_advisory_classified_hfi_id"),
        "advisory_classified_hfi",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_advisory_classified_hfi_run_type"),
        "advisory_classified_hfi",
        ["run_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_advisory_classified_hfi_threshold"),
        "advisory_classified_hfi",
        ["threshold"],
        unique=False,
    )

    op.create_table(
        "advisory_fuel_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fuel_type_id", sa.Integer(), nullable=False),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry(
                geometry_type="POLYGON",
                srid=3005,
                dimension=2,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=True,
        ),
        sa.Column("fuel_type_raster_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["fuel_type_raster_id"],
            ["fuel_type_raster.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        comment="Identify some kind of fuel type",
    )
    op.create_index(
        "idx_advisory_fuel_types_geom",
        "advisory_fuel_types",
        ["geom"],
        unique=False,
        postgresql_using="gist",
    )
    op.create_index(
        op.f("ix_advisory_fuel_types_fuel_type_id"),
        "advisory_fuel_types",
        ["fuel_type_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_advisory_fuel_types_fuel_type_raster_id"),
        "advisory_fuel_types",
        ["fuel_type_raster_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_advisory_fuel_types_id"),
        "advisory_fuel_types",
        ["id"],
        unique=False,
    )

    op.create_table(
        "advisory_elevation_stats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("advisory_shape_id", sa.Integer(), nullable=False),
        sa.Column("threshold", sa.Integer(), nullable=False),
        sa.Column("run_parameters", sa.Integer(), nullable=False),
        sa.Column("minimum", sa.Float(), nullable=False),
        sa.Column("quartile_25", sa.Float(), nullable=False),
        sa.Column("median", sa.Float(), nullable=False),
        sa.Column("quartile_75", sa.Float(), nullable=False),
        sa.Column("maximum", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["advisory_shape_id"],
            ["advisory_shapes.id"],
        ),
        sa.ForeignKeyConstraint(
            ["run_parameters"],
            ["run_parameters.id"],
        ),
        sa.ForeignKeyConstraint(
            ["threshold"],
            ["advisory_hfi_classification_threshold.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        comment="Elevation stats per fire shape by advisory threshold",
    )
    op.create_index(
        op.f("ix_advisory_elevation_stats_advisory_shape_id"),
        "advisory_elevation_stats",
        ["advisory_shape_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_advisory_elevation_stats_id"),
        "advisory_elevation_stats",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_advisory_elevation_stats_run_parameters"),
        "advisory_elevation_stats",
        ["run_parameters"],
        unique=False,
    )

    op.execute(
        """
        INSERT INTO application_data_tables (table_name, description, seed_order, last_seeded)
        VALUES (
            'advisory_fuel_types',
            'Fuel type distributions within advisory areas',
            17,
            NOW()
        )
        """
    )
