"""Add fuel raster install status

Revision ID: 6f7d3e9c2a10
Revises: a4fb7e8a1d2c
Create Date: 2026-06-10 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from wps_shared.db.models.common import TZTimeStamp


# revision identifiers, used by Alembic.
revision = "6f7d3e9c2a10"
down_revision = "a4fb7e8a1d2c"
branch_labels = None
depends_on = None

FUEL_GRID_INSTALL_SEQUENCE_TABLES = (
    "fuel_type_raster",
    "advisory_fuel_types",
    "advisory_shape_fuels",
    "combustible_area",
    "tpi_fuel_area",
)


def align_table_id_sequence(table_name: str):
    op.execute(
        f"""
        SELECT setval(
            pg_get_serial_sequence('{table_name}', 'id'),
            COALESCE(MAX(id), 1),
            MAX(id) IS NOT NULL
        )
        FROM {table_name}
        """
    )


def upgrade():
    op.add_column(
        "fuel_type_raster",
        sa.Column("install_status", sa.String(), server_default="ready", nullable=False),
    )
    op.add_column(
        "fuel_type_raster",
        sa.Column("ready_timestamp", TZTimeStamp(), nullable=True),
    )
    op.create_check_constraint(
        "ck_fuel_type_raster_install_status",
        "fuel_type_raster",
        "install_status IN ('installing', 'ready', 'failed')",
    )
    op.execute(
        """
        UPDATE fuel_type_raster
        SET ready_timestamp = create_timestamp
        WHERE install_status = 'ready'
          AND ready_timestamp IS NULL
        """
    )
    for table_name in FUEL_GRID_INSTALL_SEQUENCE_TABLES:
        align_table_id_sequence(table_name)


def downgrade():
    op.drop_constraint("ck_fuel_type_raster_install_status", "fuel_type_raster", type_="check")
    op.drop_column("fuel_type_raster", "ready_timestamp")
    op.drop_column("fuel_type_raster", "install_status")
