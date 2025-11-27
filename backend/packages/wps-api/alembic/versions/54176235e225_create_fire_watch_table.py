"""Create Fire Watch table

Revision ID: 54176235e225
Revises: 42a9dae10dca
Create Date: 2025-04-24 11:04:18.515614

"""

from alembic import op
import geoalchemy2
import sqlalchemy as sa
from wps_shared.db.models.common import TZTimeStamp

# revision identifiers, used by Alembic.
revision = "54176235e225"
down_revision = "42a9dae10dca"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "fire_watch",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("burn_location", geoalchemy2.types.Geometry(geometry_type="POINT", srid=3005, from_text="ST_GeomFromEWKT", name="geometry", nullable=False), nullable=False),
        sa.Column("burn_window_end", TZTimeStamp(), nullable=False),
        sa.Column("burn_window_start", TZTimeStamp(), nullable=False),
        sa.Column("contact_email", sa.ARRAY(sa.String()), nullable=False),
        sa.Column("create_timestamp", TZTimeStamp(), nullable=False),
        sa.Column("create_user", sa.String(), nullable=False),
        sa.Column("fire_centre", sa.Integer(), nullable=True),
        sa.Column("station_code", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("ACTIVE", "CANCELLED", "COMPLETE", "HOLD", name="burnstatusenum"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("update_timestamp", TZTimeStamp(), nullable=False),
        sa.Column("update_user", sa.String(), nullable=False),
        sa.Column(
            "fuel_type",
            sa.Enum("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C7B", "D1", "D2", "M1", "M2", "M3", "M4", "O1A", "O1B", "S1", "S2", "S3", name="fueltypeenum"),
            nullable=False,
        ),
        sa.Column("percent_conifer", sa.Float(), nullable=True),
        sa.Column("percent_dead_fir", sa.Float(), nullable=True),
        sa.Column("percent_grass_curing", sa.Float(), nullable=True),
        sa.Column("temp_min", sa.Float(), nullable=False),
        sa.Column("temp_preferred", sa.Float(), nullable=False),
        sa.Column("temp_max", sa.Float(), nullable=False),
        sa.Column("rh_min", sa.Float(), nullable=False),
        sa.Column("rh_preferred", sa.Float(), nullable=False),
        sa.Column("rh_max", sa.Float(), nullable=False),
        sa.Column("wind_speed_min", sa.Float(), nullable=False),
        sa.Column("wind_speed_preferred", sa.Float(), nullable=False),
        sa.Column("wind_speed_max", sa.Float(), nullable=False),
        sa.Column("ffmc_min", sa.Float(), nullable=False),
        sa.Column("ffmc_preferred", sa.Float(), nullable=False),
        sa.Column("ffmc_max", sa.Float(), nullable=False),
        sa.Column("dmc_min", sa.Float(), nullable=False),
        sa.Column("dmc_preferred", sa.Float(), nullable=False),
        sa.Column("dmc_max", sa.Float(), nullable=False),
        sa.Column("dc_min", sa.Float(), nullable=False),
        sa.Column("dc_preferred", sa.Float(), nullable=False),
        sa.Column("dc_max", sa.Float(), nullable=False),
        sa.Column("isi_min", sa.Float(), nullable=False),
        sa.Column("isi_preferred", sa.Float(), nullable=False),
        sa.Column("isi_max", sa.Float(), nullable=False),
        sa.Column("bui_min", sa.Float(), nullable=False),
        sa.Column("bui_preferred", sa.Float(), nullable=False),
        sa.Column("bui_max", sa.Float(), nullable=False),
        sa.Column("hfi_min", sa.Float(), nullable=False),
        sa.Column("hfi_preferred", sa.Float(), nullable=False),
        sa.Column("hfi_max", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["fire_centre"],
            ["fire_centres.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        comment="Contains parameters related to a prescribed burn.",
    )
    op.create_index(op.f("ix_fire_watch_id"), "fire_watch", ["id"], unique=False)
    op.create_index(op.f("ix_fire_watch_status"), "fire_watch", ["status"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_fire_watch_status"), table_name="fire_watch")
    op.drop_index(op.f("ix_fire_watch_id"), table_name="fire_watch")
    op.drop_table("fire_watch")
