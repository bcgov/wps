"""Combustible area 2021 and 2025

Revision ID: 305e64ecce19
Revises: c766f89f4584
Create Date: 2025-06-24 15:44:34.040991

"""

from contextlib import contextmanager

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from app.auto_spatial_advisory.calculate_combustible_land_area import (
    calculate_combustible_area_by_fire_zone,
)
from geoalchemy2.shape import to_shape
from osgeo import ogr
from sqlalchemy.orm.session import Session

# revision identifiers, used by Alembic.
revision = "305e64ecce19"
down_revision = "c766f89f4584"
branch_labels = None
depends_on = None


advisory_fuel_types_table = sa.Table(
    "advisory_fuel_types",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column("fuel_type_id", sa.Integer),
    sa.Column("geom", geoalchemy2.Geometry),
    sa.Column("fuel_type_raster_id", sa.Integer),
)

combustible_area_table = sa.Table(
    "combustible_area",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column("advisory_shape_id", sa.Integer),
    sa.Column("combustible_area", sa.Float),
    sa.Column("fuel_type_raster_id", sa.Integer),
)

fuel_type_raster_table = sa.Table(
    "fuel_type_raster",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column("version", sa.Integer),
    sa.Column("year", sa.Integer),
)

shape_table = sa.Table(
    "advisory_shapes",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column("source_identifier", sa.String),
    sa.Column("shape_type", sa.Integer),
    sa.Column("geom", geoalchemy2.Geometry),
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


def get_fire_zone_unit_shape_type_id(session: Session):
    statement = shape_type_table.select().where(shape_type_table.c.name == "fire_zone_unit")
    result = session.execute(statement).fetchone()
    return result.id


def get_fire_zone_units(session: Session, fire_zone_type_id: int):
    statement = shape_table.select().where(shape_table.c.shape_type == fire_zone_type_id)
    result = session.execute(statement).fetchall()
    return result


def get_fuel_type_polygons(session: Session, fuel_type_raster_id: int):
    stmt = advisory_fuel_types_table.select().where(
        advisory_fuel_types_table.c.fuel_type_id < 99,
        advisory_fuel_types_table.c.fuel_type_id > 0,
        advisory_fuel_types_table.c.fuel_type_raster_id == fuel_type_raster_id,
    )
    result = session.execute(stmt).fetchall()
    return result


def get_fuel_type_raster(session: Session, year: int) -> int:
    stmt = (
        fuel_type_raster_table.select()
        .where(fuel_type_raster_table.c.year == year)
        .order_by(fuel_type_raster_table.c.version.desc())
    )
    result = session.execute(stmt)
    return result.first()


@contextmanager
def get_fuel_types_from_db(session, fuel_type_raster_id):
    mem_driver = ogr.GetDriverByName("Memory")
    mem_ds = mem_driver.CreateDataSource("mem_data")
    fuel_types_layer = mem_ds.CreateLayer("fuel_types", geom_type=ogr.wkbPolygon)
    fuel_types_layer.CreateField(ogr.FieldDefn("id", ogr.OFTInteger))
    fuel_types_layer.CreateField(ogr.FieldDefn("fuel_type_id", ogr.OFTInteger))

    fuel_type_polygons = get_fuel_type_polygons(session, fuel_type_raster_id)
    for row in fuel_type_polygons:
        shapely_obj = to_shape(row.geom)

        feature = ogr.Feature(fuel_types_layer.GetLayerDefn())
        feature.SetGeometry(ogr.CreateGeometryFromWkt(shapely_obj.wkt))
        feature.SetField("id", row.id)
        feature.SetField("fuel_type_id", row.fuel_type_id)
        fuel_types_layer.CreateFeature(feature)
        feature = None

    yield fuel_types_layer
    mem_ds = None


def populate_combustible_area_for_year(session: Session, year: int):
    fuel_type_raster = get_fuel_type_raster(session, year)
    with get_fuel_types_from_db(session, fuel_type_raster.id) as fuel_types:
        fire_zone_shape_type_id = get_fire_zone_unit_shape_type_id(session)
        zone_units = get_fire_zone_units(session, fire_zone_shape_type_id)

        for _, combustible_area, advisory_shape_id in calculate_combustible_area_by_fire_zone(
            fuel_types, zone_units
        ):
            stmt = combustible_area_table.insert().values(
                advisory_shape_id=advisory_shape_id,
                combustible_area=combustible_area,
                fuel_type_raster_id=fuel_type_raster.id,
            )
            session.execute(stmt)


def depopulate_combustible_area_for_year(session: Session, year: int):
    fuel_type_raster = get_fuel_type_raster(session, 2021)
    stmt = combustible_area_table.delete().where(
        combustible_area_table.c.fuel_type_raster_id == fuel_type_raster.id
    )
    session.execute(stmt)


def upgrade():
    session = Session(bind=op.get_bind())
    # We need to calculate and add combustible area for the 2021 and 2025 fuel grids
    years = [2021, 2025]
    for year in years:
        populate_combustible_area_for_year(session, year)


def downgrade():
    session = Session(bind=op.get_bind())
    # We need to calculate and add combustible area for the 2021 and 2025 fuel grids
    years = [2021, 2025]
    for year in years:
        depopulate_combustible_area_for_year(session, year)
