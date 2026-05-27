"""SMURFI distribution groups

Revision ID: 63b52513243e
Revises: 3b9310ff54f5
Create Date: 2026-05-26 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from wps_shared.db.models.common import TZTimeStamp

# revision identifiers, used by Alembic.
revision = "63b52513243e"
down_revision = "3b9310ff54f5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "smurfi_distribution_group",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("emails", sa.ARRAY(sa.String()), nullable=False),
        sa.Column("owner_idir", sa.String(), nullable=False),
        sa.Column("created_at", TZTimeStamp(), nullable=False),
        sa.Column("updated_at", TZTimeStamp(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        comment="Named distribution groups for spot forecast email notifications.",
    )
    op.create_table(
        "spot_request_distribution_group",
        sa.Column("spot_request_id", sa.Integer(), nullable=False),
        sa.Column("distribution_group_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["distribution_group_id"], ["smurfi_distribution_group.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["spot_request_id"], ["spot_request.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("spot_request_id", "distribution_group_id"),
    )


def downgrade():
    op.drop_table("spot_request_distribution_group")
    op.drop_table("smurfi_distribution_group")
