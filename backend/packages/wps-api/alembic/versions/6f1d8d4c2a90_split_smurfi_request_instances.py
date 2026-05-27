"""split smurfi request instances

Revision ID: 6f1d8d4c2a90
Revises: 3b9310ff54f5
Create Date: 2026-05-26 10:24:00.000000

"""

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from wps_shared.db.models.common import TZTimeStamp

# revision identifiers, used by Alembic.
revision = "6f1d8d4c2a90"
down_revision = "3b9310ff54f5"
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table("spot_request", "spot_request_base")

    op.create_table(
        "spot_request_instance",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("spot_request_base_id", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column(
            "geom",
            Geometry(
                geometry_type="POINT",
                srid=3005,
                dimension=2,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=False,
        ),
        sa.Column("geographic_description", sa.String(), nullable=False),
        sa.Column("aspect", sa.String(), nullable=True),
        sa.Column("elevation", sa.Integer(), nullable=True),
        sa.Column("valley", sa.String(), nullable=True),
        sa.Column("created_at", TZTimeStamp(), nullable=False),
        sa.Column("updated_at", TZTimeStamp(), nullable=False),
        sa.ForeignKeyConstraint(["spot_request_base_id"], ["spot_request_base.id"]),
        sa.PrimaryKeyConstraint("id"),
        comment="Tracks geographic instances used by spot requests and forecasts.",
    )
    op.create_index(
        op.f("ix_spot_request_instance_spot_request_base_id"),
        "spot_request_instance",
        ["spot_request_base_id"],
        unique=False,
    )

    op.execute(
        """
        INSERT INTO spot_request_instance (
            spot_request_base_id,
            latitude,
            longitude,
            geom,
            geographic_description,
            aspect,
            elevation,
            valley,
            created_at,
            updated_at
        )
        SELECT
            id,
            ST_Y(ST_Transform(geom, 4326)),
            ST_X(ST_Transform(geom, 4326)),
            geom,
            geographic_description,
            aspect,
            elevation,
            NULL,
            created_at,
            updated_at
        FROM spot_request_base
        """
    )

    op.drop_constraint("spot_forecast_spot_request_id_fkey", "spot_forecast", type_="foreignkey")
    op.drop_index(op.f("ix_spot_forecast_spot_request_id"), table_name="spot_forecast")
    op.execute(
        """
        ALTER TABLE spot_forecast
        ALTER COLUMN fire_size TYPE FLOAT[]
        USING CASE
            WHEN fire_size IS NULL THEN NULL
            ELSE ARRAY[fire_size]
        END
        """
    )
    op.add_column("spot_forecast", sa.Column("spot_request_base_id", sa.Integer(), nullable=True))
    op.add_column(
        "spot_forecast", sa.Column("spot_request_instance_id", sa.Integer(), nullable=True)
    )
    op.execute(
        """
        UPDATE spot_forecast forecast
        SET
            spot_request_base_id = forecast.spot_request_id,
            spot_request_instance_id = instance.id
        FROM spot_request_instance instance
        WHERE instance.spot_request_base_id = forecast.spot_request_id
        """
    )
    op.alter_column("spot_forecast", "spot_request_base_id", nullable=False)
    op.alter_column("spot_forecast", "spot_request_instance_id", nullable=False)
    op.create_foreign_key(
        "spot_forecast_spot_request_base_id_fkey",
        "spot_forecast",
        "spot_request_base",
        ["spot_request_base_id"],
        ["id"],
    )
    op.create_foreign_key(
        "spot_forecast_spot_request_instance_id_fkey",
        "spot_forecast",
        "spot_request_instance",
        ["spot_request_instance_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_spot_forecast_spot_request_base_id"),
        "spot_forecast",
        ["spot_request_base_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_spot_forecast_spot_request_instance_id"),
        "spot_forecast",
        ["spot_request_instance_id"],
        unique=False,
    )
    op.drop_column("spot_forecast", "spot_request_id")

    op.drop_constraint(
        "spot_subscriber_spot_request_id_fkey", "spot_subscriber", type_="foreignkey"
    )
    op.drop_index(op.f("ix_spot_subscriber_spot_request_id"), table_name="spot_subscriber")
    op.alter_column("spot_subscriber", "spot_request_id", new_column_name="spot_request_base_id")
    op.create_foreign_key(
        "spot_subscriber_spot_request_base_id_fkey",
        "spot_subscriber",
        "spot_request_base",
        ["spot_request_base_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_spot_subscriber_spot_request_base_id"),
        "spot_subscriber",
        ["spot_request_base_id"],
        unique=False,
    )

    op.execute("ALTER TABLE spot_request_base DROP CONSTRAINT IF EXISTS chk_aspect_spot_request")
    op.drop_column("spot_request_base", "geom")
    op.drop_column("spot_request_base", "geographic_description")
    op.drop_column("spot_request_base", "elevation")
    op.drop_column("spot_request_base", "aspect")


def downgrade():
    op.add_column("spot_request_base", sa.Column("aspect", sa.String(), nullable=True))
    op.add_column("spot_request_base", sa.Column("elevation", sa.Integer(), nullable=True))
    op.add_column(
        "spot_request_base",
        sa.Column("geographic_description", sa.String(), nullable=True),
    )
    op.add_column(
        "spot_request_base",
        sa.Column(
            "geom",
            Geometry(
                geometry_type="POINT",
                srid=3005,
                dimension=2,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=True,
        ),
    )
    op.execute(
        """
        UPDATE spot_request_base base
        SET
            aspect = instance.aspect,
            elevation = instance.elevation,
            geographic_description = instance.geographic_description,
            geom = instance.geom
        FROM spot_request_instance instance
        WHERE instance.spot_request_base_id = base.id
        """
    )
    op.alter_column("spot_request_base", "geographic_description", nullable=False)
    op.alter_column("spot_request_base", "geom", nullable=False)

    op.drop_index(op.f("ix_spot_subscriber_spot_request_base_id"), table_name="spot_subscriber")
    op.drop_constraint(
        "spot_subscriber_spot_request_base_id_fkey", "spot_subscriber", type_="foreignkey"
    )
    op.alter_column("spot_subscriber", "spot_request_base_id", new_column_name="spot_request_id")
    op.create_foreign_key(
        "spot_subscriber_spot_request_id_fkey",
        "spot_subscriber",
        "spot_request_base",
        ["spot_request_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_spot_subscriber_spot_request_id"),
        "spot_subscriber",
        ["spot_request_id"],
        unique=False,
    )

    op.add_column("spot_forecast", sa.Column("spot_request_id", sa.Integer(), nullable=True))
    op.execute("UPDATE spot_forecast SET spot_request_id = spot_request_base_id")
    op.alter_column("spot_forecast", "spot_request_id", nullable=False)
    op.execute(
        """
        ALTER TABLE spot_forecast
        ALTER COLUMN fire_size TYPE FLOAT
        USING fire_size[1]
        """
    )
    op.drop_index(op.f("ix_spot_forecast_spot_request_instance_id"), table_name="spot_forecast")
    op.drop_index(op.f("ix_spot_forecast_spot_request_base_id"), table_name="spot_forecast")
    op.drop_constraint(
        "spot_forecast_spot_request_instance_id_fkey", "spot_forecast", type_="foreignkey"
    )
    op.drop_constraint(
        "spot_forecast_spot_request_base_id_fkey", "spot_forecast", type_="foreignkey"
    )
    op.drop_column("spot_forecast", "spot_request_instance_id")
    op.drop_column("spot_forecast", "spot_request_base_id")
    op.create_foreign_key(
        "spot_forecast_spot_request_id_fkey",
        "spot_forecast",
        "spot_request_base",
        ["spot_request_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_spot_forecast_spot_request_id"),
        "spot_forecast",
        ["spot_request_id"],
        unique=False,
    )

    op.drop_index(
        op.f("ix_spot_request_instance_spot_request_base_id"),
        table_name="spot_request_instance",
    )
    op.drop_table("spot_request_instance")
    op.rename_table("spot_request_base", "spot_request")
