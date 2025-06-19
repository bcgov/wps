"""Import zones

Revision ID: c04f22e31997
Revises: 17b1c787f420
Create Date: 2022-08-31 22:56:52.264112

"""
import json
from shapely import from_geojson
import os
from os import walk
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session
import geoalchemy2
from shapely import wkb


# revision identifiers, used by Alembic.
revision = 'c04f22e31997'
down_revision = '17b1c787f420'
branch_labels = None
depends_on = None


shape_type_table = sa.Table(
    "advisory_shape_types",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column("name", sa.Enum("fire_centre", "fire_zone", name="shapetypeenum"), nullable=False),
)

shape_table = sa.Table('advisory_shapes', sa.MetaData(),
                       sa.Column('id', sa.Integer),
                       sa.Column('source_identifier', sa.String),
                       sa.Column('shape_type', sa.Integer),
                       sa.Column('geom', geoalchemy2.Geometry))


def upgrade():
    session = Session(bind=op.get_bind())
    statement = shape_type_table.insert().values(name='fire_zone').returning(shape_type_table.c.id)
    result = session.execute(statement).fetchone()
    shape_type_id = result.id
    
    parent_dir = os.path.dirname(os.getcwd())
    zones_path = os.path.join(os.path.join(parent_dir, 'data'), 'zones')
    for (_, __, filenames) in walk(zones_path):
        for file in filenames:
            with open(file) as f:
                polygon_dict = json.load(f)
                fire_zone_id = polygon_dict['attributes']['MOF_FIRE_ZONE_ID']
                geom = from_geojson(json.dumps(polygon_dict))
                # Insert.
                statement = shape_table.insert().values(
                    source_identifier=fire_zone_id,
                    shape_type=shape_type_id,
                    geom=wkb.dumps(geom, hex=True, srid=3005))
                session.execute(statement)


def downgrade():
    session = Session(bind=op.get_bind())
    # Delete 'fire_zones'
    statement = shape_type_table.select().where(shape_type_table.c.name == 'fire_zone')
    result = session.execute(statement).fetchone()
    shape_type_id = result.id

    # Delete areas of type
    statement = shape_table.delete().where(shape_table.c.shape_type == shape_type_id)
    session.execute(statement)

    # Delete 'fire_zone' type
    statement = shape_type_table.delete().where(shape_type_table.c.name == 'fire_zone')
    session.execute(statement)
