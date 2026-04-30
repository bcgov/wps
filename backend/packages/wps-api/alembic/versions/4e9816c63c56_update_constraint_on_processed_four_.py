"""Update constraint on processed_four_panel_chart

Revision ID: 4e9816c63c56
Revises: 05349c55c1e2
Create Date: 2026-04-30 14:15:57.305543

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '4e9816c63c56'
down_revision = '05349c55c1e2'
branch_labels = None
depends_on = None



CHECK_CONSTRAINT_NAME = "chk_model_name_four_panel_charts"


def upgrade() -> None:
    # Drop the old constraint
    op.drop_constraint(
        CHECK_CONSTRAINT_NAME,
        "processed_four_panel_chart",
        type_="check",
    )

    # Create the updated constraint including GDPS_GEM
    op.create_check_constraint(
        CHECK_CONSTRAINT_NAME,
        "processed_four_panel_chart",
        "model IN ('GDPS', 'RDPS', 'GDPS_GEM')",
    )


def downgrade() -> None:
    # Drop the updated constraint
    op.drop_constraint(
        CHECK_CONSTRAINT_NAME,
        "processed_four_panel_chart",
        type_="check",
    )

    # Re-create the original constraint (without GDPS_GEM)
    op.create_check_constraint(
        CHECK_CONSTRAINT_NAME,
        "processed_four_panel_chart",
        "model IN ('GDPS', 'RDPS')",
    )
