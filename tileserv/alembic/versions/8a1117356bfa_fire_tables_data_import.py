"""Fire tables data import

Revision ID: 8a1117356bfa
Revises: 950a9e61996c
Create Date: 2022-11-23 14:51:50.365858

"""
from typing import Final
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Table
from sqlalchemy.orm.session import Session
from sqlalchemy.sql import select
from sqlalchemy.dialects import postgresql
import geoalchemy2
import urllib.parse
import urllib.request
import json
from shapely.geometry import shape
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.polygon import Polygon
from shapely.geometry.base import BaseGeometry
from shapely import wkb
from datetime import datetime
from models import TZTimeStamp


# revision identifiers, used by Alembic.
revision = '8a1117356bfa'
down_revision = '950a9e61996c'
branch_labels = None
depends_on = None

srid: Final = 4326

fire_zone_table = sa.Table('fire_zones', sa.MetaData(),
                           sa.Column('id', sa.Integer(), nullable=False),
                           sa.Column('feature_id', sa.Integer(), nullable=False),
                           sa.Column('geom', geoalchemy2.types.Geometry(geometry_type='MULTIPOLYGON', srid=4326,
                                                                        spatial_index=False, from_text='ST_GeomFromEWKT',
                                                                        name='geometry'), nullable=False),
                           sa.Column('create_date', TZTimeStamp(), nullable=False),
                           sa.Column('update_date', TZTimeStamp(), nullable=False),
                           sa.Column('mof_fire_zone_id', sa.Integer(), nullable=True),
                           sa.Column('mof_fire_zone_name', sa.String(), nullable=True),
                           sa.Column('mof_fire_centre_name', sa.String(), nullable=True),
                           sa.Column('headquarters_city_name', sa.String(), nullable=True),
                           sa.Column('objectid', sa.Integer(), nullable=True),
                           sa.Column('feature_area_sqm', postgresql.DOUBLE_PRECISION(), nullable=True),
                           sa.Column('feature_length_m', postgresql.DOUBLE_PRECISION(), nullable=True),
                           sa.Column('geometry.area', sa.Integer(), nullable=True),
                           sa.Column('geometry.len', sa.Integer(), nullable=True))

fire_zone_labels_table = sa.Table('fire_zones_labels', sa.MetaData(),
                                  sa.Column('id', sa.Integer(), nullable=False),
                                  sa.Column('feature_id', sa.Integer(), nullable=False),
                                  sa.Column('geom', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326,
                                                                               spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'), nullable=False),
                                  sa.Column('create_date', TZTimeStamp(), nullable=False),
                                  sa.Column('update_date', TZTimeStamp(), nullable=False),
                                  sa.Column('mof_fire_zone_id', sa.Integer(), nullable=True),
                                  sa.Column('mof_fire_zone_name', sa.String(), nullable=True),
                                  sa.Column('mof_fire_centre_name', sa.String(), nullable=True),
                                  sa.Column('headquarters_city_name', sa.String(), nullable=True),
                                  sa.Column('objectid', sa.Integer(), nullable=True),
                                  sa.Column('feature_area_sqm', postgresql.DOUBLE_PRECISION(), nullable=True),
                                  sa.Column('feature_length_m', postgresql.DOUBLE_PRECISION(), nullable=True),
                                  sa.Column('geometry.area', sa.Integer(), nullable=True),
                                  sa.Column('geometry.len', sa.Integer(), nullable=True),
                                  sa.PrimaryKeyConstraint('id'),
                                  comment='BC fire zone labels'
                                  )
fire_centre_table = sa.Table('fire_centres', sa.MetaData(),
                             sa.Column('id', sa.Integer(), nullable=False),
                             sa.Column('feature_id', sa.Integer(), nullable=False),
                             sa.Column('geom', geoalchemy2.types.Geometry(geometry_type='POLYGON', srid=4326,
                                                                          spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'), nullable=False),
                             sa.Column('create_date', TZTimeStamp(), nullable=False),
                             sa.Column('update_date', TZTimeStamp(), nullable=False),
                             sa.Column('mof_fire_centre_id', sa.Integer(), nullable=True),
                             sa.Column('mof_fire_centre_name', sa.String(), nullable=True),
                             sa.Column('objectid', sa.Integer(), nullable=True),
                             sa.Column('feature_area_sqm', postgresql.DOUBLE_PRECISION(), nullable=True),
                             sa.Column('feature_length_m', postgresql.DOUBLE_PRECISION(), nullable=True),
                             sa.Column('geometry.area', sa.Integer(), nullable=True),
                             sa.Column('geometry.len', sa.Integer(), nullable=True))

fire_centre_labels_table = sa.Table('fire_centres_labels', sa.MetaData(),
                                    sa.Column('id', sa.Integer(), nullable=False),
                                    sa.Column('feature_id', sa.Integer(), nullable=False),
                                    sa.Column('geom', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326,
                                                                                 spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'), nullable=False),
                                    sa.Column('create_date', TZTimeStamp(), nullable=False),
                                    sa.Column('update_date', TZTimeStamp(), nullable=False),
                                    sa.Column('mof_fire_centre_id', sa.Integer(), nullable=True),
                                    sa.Column('mof_fire_zone_name', sa.String(), nullable=True),
                                    sa.Column('mof_fire_centre_name', sa.String(), nullable=True),
                                    sa.Column('objectid', sa.Integer(), nullable=True),
                                    sa.Column('feature_area_sqm', postgresql.DOUBLE_PRECISION(), nullable=True),
                                    sa.Column('feature_length_m', postgresql.DOUBLE_PRECISION(), nullable=True),
                                    sa.Column('geometry.area', sa.Integer(), nullable=True),
                                    sa.Column('geometry.len', sa.Integer(), nullable=True))


def fetch_object_ids(url: str):
    """
    Fetch object list from a feature layer.
    url: layer url to fetch (e.g. https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/2)
    """
    print(f'fetching object list for {url}...')

    params = {
        'where': '1=1',
        'geometryType': 'esriGeometryEnvelope',
        'spatialRel': 'esriSpatialRelIntersects',
        # 'outSR': '102100',
        # 'outFields': '*',
        'returnGeometry': 'false',
        'returnIdsOnly': 'true',
        'f': 'json'
    }

    encode_params = urllib.parse.urlencode(params).encode("utf-8")
    print(f'{url}/query?{encode_params.decode()}')
    with urllib.request.urlopen(f'{url}/query?', encode_params) as response:
        json_data = json.loads(response.read())
    return json_data['objectIds']


def fetch_object(object_id: int, url: str):
    """
    Fetch a single object from a feature layer. We have to fetch objects one by one, because they
    can get pretty big. Big enough, that if you ask for more than one at a time, you're likely to
    encounter 500 errors.
    object_id: object id to fetch (e.g. 1)
    url: layer url to fetch (e.g. https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/2)
    """
    print(f'fetching object {object_id}')

    params = {
        'where': f'objectid={object_id}',
        'geometryType': 'esriGeometryEnvelope',
        'spatialRel': 'esriSpatialRelIntersects',
        # 'outSR': '102100',
        'outFields': '*',
        'returnGeometry': 'true',
        'returnIdsOnly': 'false',
        'f': 'geojson'
    }

    encode_params = urllib.parse.urlencode(params).encode("utf-8")
    print(f'{url}/query?{encode_params.decode()}')
    with urllib.request.urlopen(f'{url}/query?', encode_params) as response:
        json_data = json.loads(response.read())
    return json_data


def save_feature(geom_type: str, geom: BaseGeometry, srid: int, feature: dict,
                 session: Session, table_schema: Table, allow_update: bool = True):
    """ Save feature to database.
    """
    # If we're expecting multipolygons, we need to convert the polygon to a
    # multipolygon.
    if geom_type == 'MULTIPOLYGON' and isinstance(geom, Polygon):
        geom = MultiPolygon([geom])

    wkt = wkb.dumps(geom, hex=True, srid=srid)
    props = {key.lower(): value for key,
             value in feature['properties'].items()}
    values = {'feature_id': feature['id'], 'geom': wkt, **props}

    update = False
    if allow_update:
        rows = session.execute(select(table_schema).where(
            table_schema.c.feature_id == feature['id']))
        for row in rows:
            if row:
                update = True
            break

    values['update_date'] = datetime.now()
    if update:
        print('record exists, updating')
        session.execute(table_schema.update().where(
            table_schema.c.feature_id == feature['id']).values(values))
    else:
        print('create new record')
        values['create_date'] = values['update_date']
        session.execute(table_schema.insert().values(values))


def save_features_to_table(ids, url, session, table_schema, labels_table_schema):
    for object_id in ids:
        obj = fetch_object(object_id, url)

        for feature in obj['features']:
            geom = shape(feature['geometry'])

            save_feature('MULTIPOLYGON', geom, srid, feature,
                         session, table_schema)

            if isinstance(geom, Polygon):
                save_feature('POINT', geom.centroid, srid,
                             feature, session, labels_table_schema)
            elif isinstance(geom, MultiPolygon):
                # We can't update the labels for each polygon, we don't have an id
                # for it. So we have to drop them all.
                session.execute(labels_table_schema.delete(
                    labels_table_schema.c.feature_id == feature['id']))
                for polygon in geom:
                    save_feature('POINT', polygon.centroid, srid,
                                 feature, session, labels_table_schema, allow_update=False)
            else:
                raise Exception(f'unexpected geometry type: {geom}')


def upgrade() -> None:
    # ### commands auto generated by Alembic ###

    session = Session(bind=op.get_bind())
    # We fetch a list of object id's, fetching the entire layer in one go, will most likely crash
    # the server we're talking to.
    fire_zone_url: Final = "https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/8"
    fire_zone_ids = fetch_object_ids(fire_zone_url)

    fire_centre_url: Final = "https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/2"
    fire_centre_ids = fetch_object_ids(fire_centre_url)

    save_features_to_table(fire_zone_ids, fire_zone_url, session, fire_zone_table, fire_zone_labels_table)
    save_features_to_table(fire_centre_ids, fire_centre_url, session, fire_centre_table, fire_centre_labels_table)

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###

    pass
    # ### end Alembic commands ###
