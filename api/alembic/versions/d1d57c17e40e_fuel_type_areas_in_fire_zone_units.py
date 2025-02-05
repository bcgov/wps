"""Fuel type areas in fire zone units

Revision ID: d1d57c17e40e
Revises: fa4b3ecb57fe
Create Date: 2024-09-13 13:25:47.895080

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d1d57c17e40e"
down_revision = "fa4b3ecb57fe"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "advisory_shape_fuels",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("advisory_shape_id", sa.Integer(), nullable=False),
        sa.Column("fuel_type", sa.Integer(), nullable=False),
        sa.Column("fuel_area", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["advisory_shape_id"],
            ["advisory_shapes.id"],
        ),
        sa.ForeignKeyConstraint(
            ["fuel_type"],
            ["sfms_fuel_types.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        comment="Fuel types and their areas in fire zone units.",
    )
    op.create_index(op.f("ix_advisory_shape_fuels_advisory_shape_id"), "advisory_shape_fuels", ["advisory_shape_id"], unique=False)
    op.create_index(op.f("ix_advisory_shape_fuels_fuel_type"), "advisory_shape_fuels", ["fuel_type"], unique=False)
    op.create_index(op.f("ix_advisory_shape_fuels_id"), "advisory_shape_fuels", ["id"], unique=False)

    # Restore shapetypeenum as the type for the Type column of advisory_shape_types table.
    shape_type_new = sa.Enum("fire_centre", "fire_zone", "fire_zone_unit", name="shapetypeenum", create_type=False)
    conn = op.get_bind()

    shape_type_new.create(bind=conn, checkfirst=True)

    # Alter the column to use the new enum type
    op.execute("ALTER TABLE advisory_shape_types ALTER COLUMN name TYPE shapetypeenum USING name::text::shapetypeenum")
    op.execute("DROP TYPE shapetypeenum_2")


def downgrade():
    op.drop_index(op.f("ix_advisory_shape_fuels_id"), table_name="advisory_shape_fuels")
    op.drop_index(op.f("ix_advisory_shape_fuels_fuel_type"), table_name="advisory_shape_fuels")
    op.drop_index(op.f("ix_advisory_shape_fuels_advisory_shape_id"), table_name="advisory_shape_fuels")
    op.drop_table("advisory_shape_fuels")
    shape_type_new = sa.Enum("fire_centre", "fire_zone", "fire_zone_unit", name="shapetypeenum_2", create_type=False)
    conn = op.get_bind()

    shape_type_new.create(bind=conn, checkfirst=True)

    # Alter the column to use the new enum type
    op.execute("ALTER TABLE advisory_shape_types ALTER COLUMN name TYPE shapetypeenum_2 USING name::text::shapetypeenum_2")
    op.execute("DROP TYPE shapetypeenum")
