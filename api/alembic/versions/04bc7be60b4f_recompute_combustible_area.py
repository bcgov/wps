"""recompute combustible area

Revision ID: 04bc7be60b4f
Revises: 0882ed72ca2b
Create Date: 2023-01-30 13:14:29.202065

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.orm.session import Session
from app.auto_spatial_advisory.calculate_combustible_land_area import calculate_combustible_area_by_fire_zone, get_fuel_types_from_object_store


# revision identifiers, used by Alembic.
revision = '04bc7be60b4f'
down_revision = '0882ed72ca2b'
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


def get_fire_zone_shape_type_id(session: Session):
    statement = shape_type_table.select().where(shape_type_table.c.name == 'fire_zone')
    result = session.execute(statement).fetchone()
    return result.id


def get_fire_zones(session: Session, fire_zone_type_id: int):
    statement = shape_table.select().where(shape_table.c.shape_type == fire_zone_type_id)
    result = session.execute(statement).fetchall()
    return result


def upgrade():
    session = Session(bind=op.get_bind())

    with get_fuel_types_from_object_store() as fuel_types:
        # fetch all fire zones from DB
        fire_zone_shape_type_id = get_fire_zone_shape_type_id(session)
        zones = get_fire_zones(session, fire_zone_shape_type_id)

        zone_areas = calculate_combustible_area_by_fire_zone(fuel_types, zones)
        for tuple in zone_areas:
            op.execute('UPDATE advisory_shapes SET combustible_area={} WHERE source_identifier LIKE \'{}\''.format(
                tuple[1], tuple[0])
            )


def downgrade():
    session = Session(bind=op.get_bind())
    fire_zone_shape_id = get_fire_zone_shape_type_id(session)
    zones = get_fire_zones(session, fire_zone_shape_id)

    for zone in zones:
        op.execute('UPDATE advisory_shapes SET combustible_area = NULL WHERE source_identifier LIKE \'{}\''.format(
            str(zone['source_identifier'])
        ))
