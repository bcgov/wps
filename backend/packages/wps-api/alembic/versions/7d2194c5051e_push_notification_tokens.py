"""Push notification tokens

Revision ID: 7d2194c5051e
Revises: 0b46effaf3a1
Create Date: 2026-03-02 10:48:11.523814

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from wps_shared.db.models.common import TZTimeStamp

# revision identifiers, used by Alembic.
revision = '7d2194c5051e'
down_revision = '0b46effaf3a1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "device_token",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column(
            "platform", postgresql.ENUM("android", "ios", name="platformenum"), nullable=False
        ),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", TZTimeStamp(), nullable=False),
        sa.Column("updated_at", TZTimeStamp(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        comment="Device token management.",
    )
    op.create_index(op.f('ix_device_token_id'), 'device_token', ['id'], unique=False)
    op.create_index(op.f("ix_device_token_device_id"), "device_token", ["device_id"], unique=False)
    op.create_index(op.f('ix_device_token_platform'), 'device_token', ['platform'], unique=False)
    op.create_index(op.f('ix_device_token_token'), 'device_token', ['token'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_device_token_token'), table_name='device_token')
    op.drop_index(op.f('ix_device_token_platform'), table_name='device_token')
    op.drop_index(op.f('ix_device_token_id'), table_name='device_token')
    op.drop_table('device_token')
