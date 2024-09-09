"""Critical hours

Revision ID: c9e46d098c73
Revises: 6910d017b626
Create Date: 2024-08-12 16:24:00.489375

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c9e46d098c73"
down_revision = "6910d017b626"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "critical_hours",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("advisory_shape_id", sa.Integer(), nullable=False),
        sa.Column("threshold", sa.Enum("advisory", "warning", name="hficlassificationthresholdenum"), nullable=False),
        sa.Column("run_parameters", sa.Integer(), nullable=False),
        sa.Column("fuel_type", sa.Integer(), nullable=False),
        sa.Column("start_hour", sa.Integer(), nullable=False),
        sa.Column("end_hour", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["advisory_shape_id"],
            ["advisory_shapes.id"],
        ),
        sa.ForeignKeyConstraint(
            ["fuel_type"],
            ["sfms_fuel_types.id"],
        ),
        sa.ForeignKeyConstraint(
            ["run_parameters"],
            ["run_parameters.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        comment="Critical hours by firezone unit, fuel type and sfms run parameters.",
    )
    op.create_index(op.f("ix_critical_hours_advisory_shape_id"), "critical_hours", ["advisory_shape_id"], unique=False)
    op.create_index(op.f("ix_critical_hours_fuel_type"), "critical_hours", ["fuel_type"], unique=False)
    op.create_index(op.f("ix_critical_hours_id"), "critical_hours", ["id"], unique=False)
    op.create_index(op.f("ix_critical_hours_run_parameters"), "critical_hours", ["run_parameters"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_critical_hours_run_parameters"), table_name="critical_hours")
    op.drop_index(op.f("ix_critical_hours_id"), table_name="critical_hours")
    op.drop_index(op.f("ix_critical_hours_fuel_type"), table_name="critical_hours")
    op.drop_index(op.f("ix_critical_hours_advisory_shape_id"), table_name="critical_hours")
    op.drop_table("critical_hours")
