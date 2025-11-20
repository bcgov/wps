"""recompute combustible area

Revision ID: c2cd7a585bbd
Revises: 8635552697ad
Create Date: 2024-05-15 08:32:04.942965

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
revision = "c2cd7a585bbd"
down_revision = "8635552697ad"
branch_labels = None
depends_on = None


shape_type_table = sa.Table(
    "advisory_shape_types",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column(
        "name",
        sa.Enum("fire_centre", "fire_zone", "fire_zone_unit", name="shapetypeenum_2"),
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

fuel_type_table = sa.Table(
    "advisory_fuel_types",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column("fuel_type_id", sa.Integer),
    sa.Column("geom", geoalchemy2.Geometry),
)


def get_fire_zone_unit_shape_type_id(session: Session):
    statement = shape_type_table.select().where(shape_type_table.c.name == "fire_zone_unit")
    result = session.execute(statement).fetchone()
    return result.id


def get_fire_zone_units(session: Session, fire_zone_type_id: int):
    statement = shape_table.select().where(shape_table.c.shape_type == fire_zone_type_id)
    result = session.execute(statement).fetchall()
    return result


def get_fuel_type_polygons(session: Session):
    stmt = fuel_type_table.select().where(
        fuel_type_table.c.fuel_type_id < 99, fuel_type_table.c.fuel_type_id > 0
    )
    result = session.execute(stmt).fetchall()
    return result


@contextmanager
def get_fuel_types_from_db(session):
    mem_driver = ogr.GetDriverByName("Memory")
    mem_ds = mem_driver.CreateDataSource("mem_data")
    fuel_types_layer = mem_ds.CreateLayer("fuel_types", geom_type=ogr.wkbPolygon)
    fuel_types_layer.CreateField(ogr.FieldDefn("id", ogr.OFTInteger))
    fuel_types_layer.CreateField(ogr.FieldDefn("fuel_type_id", ogr.OFTInteger))

    fuel_type_polygons = get_fuel_type_polygons(session)
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


def upgrade():
    session = Session(bind=op.get_bind())

    with get_fuel_types_from_db(session) as fuel_types:
        fire_zone_shape_type_id = get_fire_zone_unit_shape_type_id(session)
        zone_units = get_fire_zone_units(session, fire_zone_shape_type_id)

        zone_areas = calculate_combustible_area_by_fire_zone(fuel_types, zone_units)
        for tuple in zone_areas:
            op.execute(
                "UPDATE advisory_shapes SET combustible_area={} WHERE source_identifier LIKE '{}'".format(
                    tuple[1], tuple[0]
                )
            )


def downgrade():
    session = Session(bind=op.get_bind())
    fire_zone_shape_id = get_fire_zone_unit_shape_type_id(session)
    zones = get_fire_zone_units(session, fire_zone_shape_id)

    for zone in zones:
        op.execute(
            "UPDATE advisory_shapes SET combustible_area = NULL WHERE source_identifier LIKE '{}'".format(
                str(zone.source_identifier)
            )
        )
