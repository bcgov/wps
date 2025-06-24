"""Add foreign key reference to fuel_type_raster.id

Revision ID: f2634e040ee5
Revises: 945a5d8e55b6
Create Date: 2025-06-18 10:07:32.280520

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f2634e040ee5"
down_revision = "945a5d8e55b6"
branch_labels = None
depends_on = None


def upgrade():
    # ### start Alembic commands ###
    op.add_column(
        "advisory_fuel_stats", sa.Column("fuel_type_raster_id", sa.Integer(), nullable=True)
    )
    op.create_index(
        op.f("ix_advisory_fuel_stats_fuel_type_raster_id"),
        "advisory_fuel_stats",
        ["fuel_type_raster_id"],
        unique=False,
    )
    op.create_foreign_key(
        "advisory_fuel_stats_fuel_type_raster_id_fkey",
        "advisory_fuel_stats",
        "fuel_type_raster",
        ["fuel_type_raster_id"],
        ["id"],
    )
    op.add_column(
        "advisory_fuel_types", sa.Column("fuel_type_raster_id", sa.Integer(), nullable=True)
    )
    op.create_index(
        op.f("ix_advisory_fuel_types_fuel_type_raster_id"),
        "advisory_fuel_types",
        ["fuel_type_raster_id"],
        unique=False,
    )
    op.create_foreign_key(
        "advisory_fuel_types_fuel_type_raster_id_fkey",
        "advisory_fuel_types",
        "fuel_type_raster",
        ["fuel_type_raster_id"],
        ["id"],
    )
    op.add_column(
        "advisory_hfi_percent_conifer",
        sa.Column("fuel_type_raster_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        op.f("ix_advisory_hfi_percent_conifer_fuel_type_raster_id"),
        "advisory_hfi_percent_conifer",
        ["fuel_type_raster_id"],
        unique=False,
    )
    op.create_foreign_key(
        "advisory_hfi_percent_conifer_fuel_type_raster_id_fkey",
        "advisory_hfi_percent_conifer",
        "fuel_type_raster",
        ["fuel_type_raster_id"],
        ["id"],
    )
    op.add_column(
        "advisory_shape_fuels", sa.Column("fuel_type_raster_id", sa.Integer(), nullable=True)
    )
    op.create_index(
        op.f("ix_advisory_shape_fuels_fuel_type_raster_id"),
        "advisory_shape_fuels",
        ["fuel_type_raster_id"],
        unique=False,
    )
    op.create_foreign_key(
        "advisory_shape_fuels_fuel_type_raster_id_fkey",
        "advisory_shape_fuels",
        "fuel_type_raster",
        ["fuel_type_raster_id"],
        ["id"],
    )
    op.add_column("critical_hours", sa.Column("fuel_type_raster_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_critical_hours_fuel_type_raster_id"),
        "critical_hours",
        ["fuel_type_raster_id"],
        unique=False,
    )
    op.create_foreign_key(
        "critical_hours_fuel_type_raster_id_fkey",
        "critical_hours",
        "fuel_type_raster",
        ["fuel_type_raster_id"],
        ["id"],
    )
    op.add_column("tpi_fuel_area", sa.Column("fuel_type_raster_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_tpi_fuel_area_fuel_type_raster_id"),
        "tpi_fuel_area",
        ["fuel_type_raster_id"],
        unique=False,
    )
    op.create_foreign_key(
        "tpi_fuel_area_fuel_type_raster_id_fkey",
        "tpi_fuel_area",
        "fuel_type_raster",
        ["fuel_type_raster_id"],
        ["id"],
    )
    # ### end Alembic commands ###


def downgrade():
    # ### start Alembic commands ###
    op.drop_constraint(
        "tpi_fuel_area_fuel_type_raster_id_fkey", "tpi_fuel_area", type_="foreignkey"
    )
    op.drop_index(op.f("ix_tpi_fuel_area_fuel_type_raster_id"), table_name="tpi_fuel_area")
    op.drop_column("tpi_fuel_area", "fuel_type_raster_id")
    op.drop_constraint(
        "critical_hours_fuel_type_raster_id_fkey", "critical_hours", type_="foreignkey"
    )
    op.drop_index(op.f("ix_critical_hours_fuel_type_raster_id"), table_name="critical_hours")
    op.drop_column("critical_hours", "fuel_type_raster_id")
    op.drop_constraint(
        "advisory_shape_fuels_fuel_type_raster_id_fkey", "advisory_shape_fuels", type_="foreignkey"
    )
    op.drop_index(
        op.f("ix_advisory_shape_fuels_fuel_type_raster_id"), table_name="advisory_shape_fuels"
    )
    op.drop_column("advisory_shape_fuels", "fuel_type_raster_id")
    op.drop_constraint(
        "advisory_hfi_percent_conifer_fuel_type_raster_id_fkey",
        "advisory_hfi_percent_conifer",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_advisory_hfi_percent_conifer_fuel_type_raster_id"),
        table_name="advisory_hfi_percent_conifer",
    )
    op.drop_column("advisory_hfi_percent_conifer", "fuel_type_raster_id")

    op.drop_constraint(
        "advisory_fuel_types_fuel_type_raster_id_fkey", "advisory_fuel_types", type_="foreignkey"
    )
    op.drop_index(
        op.f("ix_advisory_fuel_types_fuel_type_raster_id"), table_name="advisory_fuel_types"
    )
    op.drop_column("advisory_fuel_types", "fuel_type_raster_id")

    op.drop_constraint(
        "advisory_fuel_stats_fuel_type_raster_id_fkey", "advisory_fuel_stats", type_="foreignkey"
    )
    op.drop_index(
        op.f("ix_advisory_fuel_stats_fuel_type_raster_id"), table_name="advisory_fuel_stats"
    )
    op.drop_column("advisory_fuel_stats", "fuel_type_raster_id")
    # ### end Alembic commands ###
