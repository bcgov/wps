"""Fuel area per TPI class

Revision ID: 1e6932096921
Revises: 4014ddf1f874
Create Date: 2025-01-21 09:48:41.621501

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "1e6932096921"
down_revision = "4014ddf1f874"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tpi_fuel_area",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("advisory_shape_id", sa.Integer(), nullable=False),
        sa.Column("tpi_class", sa.Enum("valley_bottom", "mid_slope", "upper_slope", name="tpiclassenum"), nullable=False),
        sa.Column("fuel_area", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["advisory_shape_id"],
            ["advisory_shapes.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        comment="Combustible area in each TPI class per fire zone unit.",
    )
    op.create_index(op.f("ix_tpi_fuel_area_advisory_shape_id"), "tpi_fuel_area", ["advisory_shape_id"], unique=False)
    op.create_index(op.f("ix_tpi_fuel_area_id"), "tpi_fuel_area", ["id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_tpi_fuel_area_id"), table_name="tpi_fuel_area")
    op.drop_index(op.f("ix_tpi_fuel_area_advisory_shape_id"), table_name="tpi_fuel_area")
    op.drop_table("tpi_fuel_area")
