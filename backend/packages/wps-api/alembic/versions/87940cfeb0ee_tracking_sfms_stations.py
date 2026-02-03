"""Tracking SFMS stations

Revision ID: 87940cfeb0ee
Revises: a1b2c3d4e5f6
Create Date: 2026-02-02 16:25:49.085391

"""

import sqlalchemy as sa
from alembic import op
from wps_shared.db.models.common import TZTimeStamp

# revision identifiers, used by Alembic.
revision = "87940cfeb0ee"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sfms_stations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_type", sa.String(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("run_date", TZTimeStamp(), nullable=False),
        sa.Column("stations", sa.ARRAY(sa.Integer()), nullable=False),
        sa.Column("station_count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        comment="Tracks SFMS job runs and the stations used.",
    )
    op.create_index(op.f("ix_sfms_stations_id"), "sfms_stations", ["id"], unique=False)
    op.create_index(op.f("ix_sfms_stations_run_date"), "sfms_stations", ["run_date"], unique=False)
    op.create_index(op.f("ix_sfms_stations_run_type"), "sfms_stations", ["run_type"], unique=False)
    op.create_index(
        op.f("ix_sfms_stations_target_date"), "sfms_stations", ["target_date"], unique=False
    )
    op.add_column("sfms_run_log", sa.Column("sfms_stations_id", sa.Integer(), nullable=False))
    op.create_index(op.f("ix_sfms_run_log_id"), "sfms_run_log", ["id"], unique=False)
    op.create_foreign_key(
        "fk_sfms_run_log_sfms_stations",
        "sfms_run_log",
        "sfms_stations",
        ["sfms_stations_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint("fk_sfms_run_log_sfms_stations", "sfms_run_log", type_="foreignkey")
    op.drop_index(op.f("ix_sfms_run_log_id"), table_name="sfms_run_log")
    op.drop_column("sfms_run_log", "sfms_stations_id")
    op.drop_index(op.f("ix_sfms_stations_target_date"), table_name="sfms_stations")
    op.drop_index(op.f("ix_sfms_stations_run_type"), table_name="sfms_stations")
    op.drop_index(op.f("ix_sfms_stations_run_date"), table_name="sfms_stations")
    op.drop_index(op.f("ix_sfms_stations_id"), table_name="sfms_stations")
    op.drop_table("sfms_stations")
