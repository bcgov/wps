"""create advisory_hfi_percent_conifer table

Revision ID: 08799237842e
Revises: 2cf10021c5f1
Create Date: 2025-03-05 14:50:47.127461

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "08799237842e"
down_revision = "2cf10021c5f1"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic ###

    op.create_table(
        "advisory_hfi_percent_conifer",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("advisory_shape_id", sa.Integer(), nullable=False),
        sa.Column("fuel_type", sa.Integer(), nullable=False),
        sa.Column("run_parameters", sa.Integer(), nullable=False),
        sa.Column("min_percent_conifer", sa.Integer(), nullable=True),
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
        comment="Minimum percent conifer for HFI above advisory level, per fire zone. min_percent_conifer refers to the minimum percent of conifer trees in a fire zone that coincides with hfi pixels exceeding an HFI value of 4000.",
    )
    op.create_index(op.f("ix_advisory_hfi_percent_conifer_advisory_shape_id"), "advisory_hfi_percent_conifer", ["advisory_shape_id"], unique=False)
    op.create_index(op.f("ix_advisory_hfi_percent_conifer_id"), "advisory_hfi_percent_conifer", ["id"], unique=False)
    op.create_index(op.f("ix_advisory_hfi_percent_conifer_run_parameters"), "advisory_hfi_percent_conifer", ["run_parameters"], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic ###

    op.drop_index(op.f("ix_advisory_hfi_percent_conifer_run_parameters"), table_name="advisory_hfi_percent_conifer")
    op.drop_index(op.f("ix_advisory_hfi_percent_conifer_id"), table_name="advisory_hfi_percent_conifer")
    op.drop_index(op.f("ix_advisory_hfi_percent_conifer_advisory_shape_id"), table_name="advisory_hfi_percent_conifer")
    op.drop_table("advisory_hfi_percent_conifer")

    # ### end Alembic commands ###
