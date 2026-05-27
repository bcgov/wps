"""add spot forecast type

Revision ID: c2a830d3218e
Revises: 6f1d8d4c2a90
Create Date: 2026-05-27 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c2a830d3218e"
down_revision = "6f1d8d4c2a90"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("spot_forecast", sa.Column("forecast_type", sa.String(), nullable=True))
    op.execute(
        """
        UPDATE spot_forecast forecast
        SET forecast_type = COALESCE(request_base.request_type, 'Full')
        FROM spot_request_base request_base
        WHERE request_base.id = forecast.spot_request_base_id
        """
    )
    op.execute("UPDATE spot_forecast SET forecast_type = 'Full' WHERE forecast_type IS NULL")
    op.alter_column("spot_forecast", "forecast_type", nullable=False)
    op.create_check_constraint(
        "chk_forecast_type_spot_forecast",
        "spot_forecast",
        "forecast_type IN ('Full', 'Mini')",
    )


def downgrade():
    op.drop_constraint("chk_forecast_type_spot_forecast", "spot_forecast", type_="check")
    op.drop_column("spot_forecast", "forecast_type")
