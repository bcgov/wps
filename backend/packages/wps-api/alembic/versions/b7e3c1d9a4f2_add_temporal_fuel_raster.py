"""Add temporal fuel raster table

Revision ID: b7e3c1d9a4f2
Revises: 2a6d8f4c1b73
Create Date: 2026-10-05 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from wps_shared.db.models.common import TZTimeStamp

# revision identifiers, used by Alembic.
revision = "b7e3c1d9a4f2"
down_revision = "2a6d8f4c1b73"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "temporal_fuel_raster",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fuel_type_raster_id", sa.Integer(), nullable=False),
        sa.Column("for_date", sa.Date(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("object_store_path", sa.String(), nullable=False),
        sa.Column("fuel_codes_lookup_path", sa.String(), nullable=False),
        sa.Column("content_hash", sa.String(), nullable=False),
        sa.Column("green_up_on_hash", sa.String(), nullable=False),
        sa.Column("green_up_off_hash", sa.String(), nullable=False),
        sa.Column("create_timestamp", TZTimeStamp(), nullable=False),
        sa.ForeignKeyConstraint(["fuel_type_raster_id"], ["fuel_type_raster.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("for_date", "version"),
        comment="Daily temporal fuel type rasters.",
    )
    op.create_index(
        op.f("ix_temporal_fuel_raster_fuel_type_raster_id"),
        "temporal_fuel_raster",
        ["fuel_type_raster_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_temporal_fuel_raster_for_date"),
        "temporal_fuel_raster",
        ["for_date"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_temporal_fuel_raster_for_date"), table_name="temporal_fuel_raster")
    op.drop_index(
        op.f("ix_temporal_fuel_raster_fuel_type_raster_id"), table_name="temporal_fuel_raster"
    )
    op.drop_table("temporal_fuel_raster")
