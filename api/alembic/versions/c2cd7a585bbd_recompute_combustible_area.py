"""recompute combustible area

Revision ID: c2cd7a585bbd
Revises: 8635552697ad
Create Date: 2024-05-15 08:32:04.942965

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.orm.session import Session
from contextlib import contextmanager
from osgeo import ogr, gdal
from app.db.database import DB_READ_STRING
from app.auto_spatial_advisory.calculate_combustible_land_area import calculate_combustible_area_by_fire_zone

# revision identifiers, used by Alembic.
revision = 'c2cd7a585bbd'
down_revision = '8635552697ad'
branch_labels = None
depends_on = None


shape_type_table = sa.Table('advisory_shape_types', sa.MetaData(),
                            sa.Column('id', sa.Integer),
                            sa.Column('name', sa.String))

shape_table = sa.Table('advisory_shapes', sa.MetaData(),
                       sa.Column('id', sa.Integer),
                       sa.Column('source_identifier', sa.String),
                       sa.Column('shape_type', sa.Integer),
                       sa.Column('geom', geoalchemy2.Geometry))


def get_fire_zone_unit_shape_type_id(session: Session):
    statement = shape_type_table.select().where(shape_type_table.c.name == 'fire_zone_unit')
    result = session.execute(statement).fetchone()
    return result.id


def get_fire_zone_units(session: Session, fire_zone_type_id: int):
    statement = shape_table.select().where(shape_table.c.shape_type == fire_zone_type_id)
    result = session.execute(statement).fetchall()
    return result


@contextmanager
def get_fuel_types_from_db():
    data_source = ogr.Open(DB_READ_STRING, gdal.GA_ReadOnly)
    fuel_types_layer = data_source.GetLayerByName('advisory_fuel_types')

    # Filter out non-combustible fuel types
    fuel_types_layer.SetAttributeFilter('"fuel_type_id" > 0 and "fuel_type_id" < 99')

    yield fuel_types_layer
    data_source = None


def upgrade():
    session = Session(bind=op.get_bind())

    with get_fuel_types_from_db() as fuel_types:
        # fetch all fire zones from DB
        fire_zone_shape_type_id = get_fire_zone_unit_shape_type_id(session)
        zone_units = get_fire_zone_units(session, fire_zone_shape_type_id)

        zone_areas = calculate_combustible_area_by_fire_zone(fuel_types, zone_units)
        for tuple in zone_areas:
            op.execute('UPDATE advisory_shapes SET combustible_area={} WHERE source_identifier LIKE \'{}\''.format(
                tuple[1], tuple[0])
            )


def downgrade():
    session = Session(bind=op.get_bind())
    fire_zone_shape_id = get_fire_zone_unit_shape_type_id(session)
    zones = get_fire_zone_units(session, fire_zone_shape_id)

    for zone in zones:
        op.execute('UPDATE advisory_shapes SET combustible_area = NULL WHERE source_identifier LIKE \'{}\''.format(
            str(zone.source_identifier)
        ))
