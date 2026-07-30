"""Ensure each device id has one token row.

Revision ID: e4a9f2c7d1b6
Revises: cbde211a0c72
Create Date: 2026-07-30 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "e4a9f2c7d1b6"
down_revision = "cbde211a0c72"
branch_labels = None
depends_on = None


def upgrade():
    # keep the active row for each device, falling back to the most recently updated row
    op.execute("""
        WITH ranked_device_tokens AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY device_id
                    ORDER BY is_active DESC, updated_at DESC, id DESC
                ) AS row_number
            FROM device_token
        )
        DELETE FROM notification_settings
        WHERE device_token_id IN (
            SELECT id
            FROM ranked_device_tokens
            WHERE row_number > 1
        )
    """)

    op.execute("""
        WITH ranked_device_tokens AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY device_id
                    ORDER BY is_active DESC, updated_at DESC, id DESC
                ) AS row_number
            FROM device_token
        )
        DELETE FROM device_token
        WHERE id IN (
            SELECT id
            FROM ranked_device_tokens
            WHERE row_number > 1
        )
    """)

    op.create_unique_constraint("uq_device_token_device_id", "device_token", ["device_id"])


def downgrade():
    op.drop_constraint("uq_device_token_device_id", "device_token", type_="unique")
