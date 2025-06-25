"""Populate advisory_shape_fuels with 2021 and 2025 data

Revision ID: e94f982e723c
Revises: 0eb9e7f65a50
Create Date: 2025-06-23 18:42:16.042546

"""

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from app.auto_spatial_advisory.fuel_type_area import calculate_fuel_type_areas_per_zone
from app.auto_spatial_advisory.fuel_type_layer import fuel_type_iterator_by_key
from sqlalchemy.orm.session import Session

from wps_shared import config
from wps_shared.db.models.auto_spatial_advisory import AdvisoryShapeFuels
from wps_shared.geospatial.fuel_raster import get_versioned_fuel_raster_key
from wps_shared.sfms.raster_addresser import RasterKeyAddresser

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
    sa.Column("advisory_shape_id", sa.Integer),
    sa.Column("fuel_type", sa.Integer),
    sa.Column("fuel_area", sa.Float),
    sa.Column("fuel_type_raster_id", sa.Integer),
)

shape_type_table = sa.Table(
    "advisory_shape_types",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column(
        "name",
        sa.Enum("fire_centre", "fire_zone", "fire_zone_unit", name="shapetypeenum"),
        nullable=False,
    ),
)

shape_table = sa.Table(
    "advisory_shapes",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column("source_identifier", sa.String),
    sa.Column("shape_type", sa.Integer),
    sa.Column("geom", geoalchemy2.Geometry),
)


sfms_fuel_types_table = sa.Table(
    "sfms_fuel_types",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column("fuel_type_id", sa.Integer),
    sa.Column("fuel_type_code", sa.String),
)


def get_fire_zone_unit_shape_type_id(session: Session):
    statement = shape_type_table.select().where(shape_type_table.c.name == "fire_zone_unit")
    result = session.execute(statement).fetchone()
    return result.id


def get_fire_zone_units(session: Session, fire_zone_type_id: int):
    statement = shape_table.select().where(shape_table.c.shape_type == fire_zone_type_id)
    result = session.execute(statement).fetchall()
    return result


def get_fuel_type_raster(session: Session, year: int) -> int:
    stmt = (
        fuel_type_raster_table.select()
        .where(fuel_type_raster_table.c.year == year)
        .order_by(fuel_type_raster_table.c.version.desc())
    )
    result = session.execute(stmt)
    return result.first()


def get_sfms_fuel_type_records(session: Session):
    stmt = sfms_fuel_types_table.select()
    result = session.execute(stmt)
    return result.all()


def get_sfms_fuel_types_id_dict(session: Session):
    sfms_fuel_types = get_sfms_fuel_type_records(session)
    sfms_fuel_types_dict = {}
    for sfms_fuel_type in sfms_fuel_types:
        sfms_fuel_types_dict[sfms_fuel_type.fuel_type_id] = sfms_fuel_type.id
    return sfms_fuel_types_dict


def populate_advisory_fuel_types_table_by_year(session: Session, year):
    bucket = config.get("OBJECT_STORE_BUCKET")
    fuel_type_raster = get_fuel_type_raster(session, year)
    fuel_type_raster_key = f"/vsis3/{bucket}/{fuel_type_raster.object_store_path}"
    for fuel_type_id, geom in fuel_type_iterator_by_key(fuel_type_raster_key):
        statement = advisory_fuel_types_table.insert().values(
            fuel_type_id=fuel_type_id, fuel_type_raster_id=fuel_type_raster.id, geom=geom
        )
        session.execute(statement)


def depopulate_advisory_fuel_types_table_by_year(session, year):
    fuel_type_raster = get_fuel_type_raster(session, year)
    stmt = advisory_fuel_types_table.delete().where(
        advisory_fuel_types_table.c.fuel_type_raster_id == fuel_type_raster.id
    )
    session.execute(stmt)


def depopulate_advisory_shape_fuels_by_year(session: Session, year):
    fuel_type_raster = get_fuel_type_raster(session, year)
    stmt = advisory_shape_fuels_table.delete().where(
        advisory_shape_fuels_table.c.fuel_type_raster_id == fuel_type_raster.id
    )
    session.execute(stmt)


def calculate_fuel_type_areas_for_year(session: Session, year: int):
    fuel_type_raster = get_fuel_type_raster(session, year)
    fuel_raster_key = get_versioned_fuel_raster_key(
        RasterKeyAddresser(), fuel_type_raster.object_store_path
    )
    shape_type_id = get_fire_zone_unit_shape_type_id(session)
    zones = get_fire_zone_units(session, shape_type_id)
    sfms_fuel_types_dict = get_sfms_fuel_types_id_dict(session)
    all_zone_data = calculate_fuel_type_areas_per_zone(fuel_raster_key, zones)

    for zone_data in all_zone_data:
        for advisory_shape_id, fuel_type_id, fuel_area in zone_data:
            advisory_shape_fuel = AdvisoryShapeFuels(
                advisory_shape_id=advisory_shape_id,
                fuel_type=sfms_fuel_types_dict[fuel_type_id],
                fuel_area=fuel_area,
                fuel_type_raster_id=fuel_type_raster.id,
            )
            session.add(advisory_shape_fuel)
    session.commit()


def upgrade():
    session = Session(bind=op.get_bind())
    # Process the 2021 and 2025 fuel grids
    years = [2021, 2025]
    for year in years:
        # Add advisory_fuel_type data
        populate_advisory_fuel_types_table_by_year(session, year)
        # Calculate and store advisory_shape_fuel data
        calculate_fuel_type_areas_for_year(session, year)


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
