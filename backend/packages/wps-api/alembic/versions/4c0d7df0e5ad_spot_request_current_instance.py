"""spot request current instance

Revision ID: 4c0d7df0e5ad
Revises: c2a830d3218e
Create Date: 2026-06-01 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4c0d7df0e5ad"
down_revision = "63b52513243e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "spot_request_base",
        sa.Column("current_request_instance_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "spot_request_base_current_request_instance_id_fkey",
        "spot_request_base",
        "spot_request_instance",
        ["current_request_instance_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_spot_request_base_current_request_instance_id"),
        "spot_request_base",
        ["current_request_instance_id"],
        unique=False,
    )
    op.execute(
        """
        UPDATE spot_request_base request
        SET current_request_instance_id = instance.id
        FROM (
            SELECT DISTINCT ON (spot_request_base_id)
                id,
                spot_request_base_id
            FROM spot_request_instance
            ORDER BY spot_request_base_id, created_at, id
        ) instance
        WHERE instance.spot_request_base_id = request.id
        """
    )


def downgrade():
    op.drop_index(
        op.f("ix_spot_request_base_current_request_instance_id"),
        table_name="spot_request_base",
    )
    op.drop_constraint(
        "spot_request_base_current_request_instance_id_fkey",
        "spot_request_base",
        type_="foreignkey",
    )
    op.drop_column("spot_request_base", "current_request_instance_id")
