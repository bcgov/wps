"""Import zones

Revision ID: c04f22e31997
Revises: 17b1c787f420
Create Date: 2022-08-31 22:56:52.264112

"""
from typing import Final
import tempfile
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session
import geoalchemy2
from shapely.geometry import MultiPolygon, Polygon
from shapely import wkb
from app.utils import esri


# revision identifiers, used by Alembic.
revision = 'c04f22e31997'
down_revision = '17b1c787f420'
branch_labels = None
depends_on = None


area_type_table = sa.Table('advisory_area_types', sa.MetaData(),
                           sa.Column('id', sa.Integer),
                           sa.Column('name', sa.String))

area_table = sa.Table('advisory_areas', sa.MetaData(),
                      sa.Column('id', sa.Integer),
                      sa.Column('external_identifier', sa.String),
                      sa.Column('area_type', sa.Integer),
                      sa.Column('geom', geoalchemy2.Geometry))


def upgrade():
    session = Session(bind=op.get_bind())
    statement = area_type_table.insert().values(name='fire_zone').returning(area_type_table.c.id)
    result = session.execute(statement).fetchone()
    area_type_id = result.id

    # We fetch a list of object id's, fetching the entire layer in one go, will most likely crash
    # the server we're talking to.
    zone_url: Final = "https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/8"
    zone_ids = esri.fetch_object_list(zone_url)
    for object_id in zone_ids:
        # Fetch each object in turn.
        obj = esri.fetch_object(object_id, zone_url)
        for feature in obj.get('features', []):
            attributes = feature.get('attributes', {})
            # Each zone is uniquely identified by a fire zone id.
            mof_fire_zone_id = attributes.get('MOF_FIRE_ZONE_ID')
            fire_zone_id = str(int(mof_fire_zone_id))
            geometry = feature.get('geometry', {})
            rings = geometry.get('rings', [[]])
            polygons = []
            for ring in rings:
                # Simplify each polygon to 1000 meters, preserving topology.
                polygons.append(Polygon(ring).simplify(1000, preserve_topology=True))
            geom = MultiPolygon(polygons)
            # Insert.
            statement = area_table.insert().values(
                external_identifier=fire_zone_id,
                area_type=area_type_id,
                geom=wkb.dumps(geom, hex=True, srid=3005))
            session.execute(statement)


def downgrade():
    session = Session(bind=op.get_bind())
    # Delete 'fire_zones'
    statement = area_type_table.select().where(area_type_table.c.name == 'fire_zone')
    result = session.execute(statement).fetchone()
    area_type_id = result.id

    # Delete areas of type
    statement = area_table.delete().where(area_table.c.area_type == area_type_id)
    session.execute(statement)

    # Delete 'fire_zone' type
    statement = area_type_table.delete().where(area_type_table.c.name == 'fire_zone')
    session.execute(statement)
