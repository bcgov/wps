"""compute zone unit combustible area

Revision ID: d5115b761e39
Revises: 5b745fe0bd7a
Create Date: 2023-10-31 12:24:36.889483

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.orm.session import Session
from app.auto_spatial_advisory.calculate_combustible_land_area import calculate_combustible_area_by_fire_zone, get_fuel_types_from_object_store

# revision identifiers, used by Alembic.
revision = 'd5115b761e39'
down_revision = '5b745fe0bd7a'
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


def upgrade():
    session = Session(bind=op.get_bind())

    with get_fuel_types_from_object_store() as fuel_types:
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
