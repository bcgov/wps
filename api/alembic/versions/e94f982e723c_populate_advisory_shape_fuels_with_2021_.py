"""Populate advisory_shape_fuels with 2021 and 2025 data

Revision ID: e94f982e723c
Revises: 0eb9e7f65a50
Create Date: 2025-06-23 18:42:16.042546

"""

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from app.auto_spatial_advisory.fuel_type_layer import fuel_type_iterator_by_key
from app.jobs.fuel_type_areas_per_zone import FuelTypeAreasJob
from sqlalchemy.orm.session import Session
from sqlalchemy.util import await_only

from wps_shared import config

# revision identifiers, used by Alembic.
revision = "e94f982e723c"
down_revision = "0eb9e7f65a50"
branch_labels = None
depends_on = None


advisory_fuel_types_table = sa.Table(
    "advisory_fuel_types",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column("fuel_type_id", sa.Integer),
    sa.Column("fuel_type_raster_id", sa.Integer),
    sa.Column("geom", geoalchemy2.Geometry),
)

fuel_type_raster_table = sa.Table(
    "fuel_type_raster",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column("object_store_path", sa.String),
    sa.Column("version", sa.Integer),
    sa.Column("year", sa.Integer),
)

advisory_shape_fuels_table = sa.Table(
    "advisory_shape_fuels",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column("fuel_type_raster_id", sa.Integer),
)


def get_fuel_type_raster(session: Session, year: int) -> int:
    stmt = (
        fuel_type_raster_table.select()
        .where(fuel_type_raster_table.c.year == year)
        .order_by(fuel_type_raster_table.c.version.desc())
    )
    result = session.execute(stmt)
    return result.first()


def populate_advisory_fuel_types_table_by_year(session: Session, year):
    bucket = config.get("OBJECT_STORE_BUCKET")
    fuel_type_raster = get_fuel_type_raster(session, year)
    fuel_type_raster_key = f"/vsis3/{bucket}/{fuel_type_raster.object_store_path}"
    for fuel_type_id, geom in fuel_type_iterator_by_key(fuel_type_raster_key):
        statement = advisory_fuel_types_table.insert().values(
            fuel_type_id=fuel_type_id, fuel_type_raster_id=fuel_type_raster.id, geom=geom
        )
        op.execute(statement)


def depopulate_advisory_fuel_types_table_by_year(session, year):
    fuel_type_raster = get_fuel_type_raster(session, year)
    stmt = advisory_fuel_types_table.delete().where(
        advisory_fuel_types_table.c.fuel_type_raster_id == fuel_type_raster.id
    )
    op.execute(stmt)


def depopulate_advisory_shape_fuels_by_year(session: Session, year):
    fuel_type_raster = get_fuel_type_raster(session, year)
    stmt = advisory_shape_fuels_table.delete().where(
        advisory_shape_fuels_table.c.fuel_type_raster_id == fuel_type_raster.id
    )
    session.execute(stmt)


def upgrade():
    session = Session(bind=op.get_bind())
    # Add fba2021.tif fuel grid data to advisory_fuel_types by iterating through the fuel types and
    # inserting them.
    populate_advisory_fuel_types_table_by_year(session, 2021)
    # Add fba2025.tif fuel grid data to advisory_fuel_types by iterating through the fuel types and
    # inserting them.
    populate_advisory_fuel_types_table_by_year(session, 2025)
    fuel_type_areas_job = FuelTypeAreasJob()
    # Populate advisory_shape_fuels with 2021 data
    await_only(fuel_type_areas_job.calculate_fuel_type_areas_per_zone(2021, None))
    # Populate advisory_shape_fuels with 2025 data
    await_only(fuel_type_areas_job.calculate_fuel_type_areas_per_zone(2025, None))


def downgrade():
    session = Session(bind=op.get_bind())
    # Remove advisory_fuel_types data from 2021
    depopulate_advisory_fuel_types_table_by_year(session, 2021)
    # Remove advisory_fuel_types data from 2025
    depopulate_advisory_fuel_types_table_by_year(session, 2025)
    # Remove advisory_shape_fuels data for 2021
    depopulate_advisory_shape_fuels_by_year(session, 2021)
    # Remove advisory_shape_fuels data for 2025
    depopulate_advisory_shape_fuels_by_year(session, 2025)
