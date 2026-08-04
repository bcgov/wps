"""Ensure each device id has one token row.

Revision ID: e4a9f2c7d1b6
Revises: cbde211a0c72
Create Date: 2026-07-30 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from wps_shared.db.models.common import TZTimeStamp

# revision identifiers, used by Alembic.
revision = "e4a9f2c7d1b6"
down_revision = "cbde211a0c72"
branch_labels = None
depends_on = None

device_token = sa.table(
    "device_token",
    sa.column("id", sa.Integer()),
    sa.column("device_id", sa.String()),
    sa.column("is_active", sa.Boolean()),
    sa.column("updated_at", TZTimeStamp()),
)
notification_settings = sa.table(
    "notification_settings",
    sa.column("id", sa.Integer()),
    sa.column("device_token_id", sa.Integer()),
)


def _stale_device_token_ids() -> sa.Select:
    """Select every duplicate device token row that should not be kept."""
    row_number = (
        sa.func.row_number()
        .over(
            partition_by=device_token.c.device_id,
            order_by=[
                device_token.c.is_active.desc(),
                device_token.c.updated_at.desc(),
                device_token.c.id.desc(),
            ],
        )
        .label("row_number")
    )
    ranked = sa.select(device_token.c.id, row_number).cte("ranked_device_tokens")
    return sa.select(ranked.c.id).where(ranked.c.row_number > 1)


def upgrade():
    stale_ids = _stale_device_token_ids()
    op.execute(
        notification_settings.delete().where(notification_settings.c.device_token_id.in_(stale_ids))
    )
    op.execute(device_token.delete().where(device_token.c.id.in_(stale_ids)))

    op.create_unique_constraint("uq_device_token_device_id", "device_token", ["device_id"])


def downgrade():
    op.drop_constraint("uq_device_token_device_id", "device_token", type_="unique")
