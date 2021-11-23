"""Import vernon thessian polygons

Revision ID: ae77388bb574
Revises: 2ca7085c412b
Create Date: 2021-11-22 13:48:10.405804

"""
from datetime import datetime
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String
import geoalchemy2
import os
import json
from osgeo import ogr
from shapely.geometry import shape
from shapely import wkb


# revision identifiers, used by Alembic.
revision = 'ae77388bb574'
down_revision = '2ca7085c412b'
branch_labels = None
depends_on = None


file_path = os.getcwd() + '/alembic/vernon_area_prototype/VernonFZBATPolys.shp'


def upgrade():
    file = ogr.Open(file_path)

    # We're only expecting 1 layer
    layer = file.GetLayer(0)

    # Iterate through all the features.
    feature = layer.GetNextFeature()

    thessian_polygon_area = table('thessian_polygon_area',
        column('station_code', String),
        column('geom', geoalchemy2.types.Geometry),
        column('create_date', sa.TIMESTAMP),
        column('update_date', sa.TIMESTAMP)
    )

    while feature is not None:
        # convert the feature to geojson - it's just easier to work with that way.
        geojson = json.loads(feature.ExportToJson())
        
        # extract the station code
        station_code = geojson["properties"]["STATION_CO"]
        # extract the geometry
        geom = shape(geojson["geometry"])
        # we need the srid in the wkt (if we just go geom.wkt - we sadly don't get it
        wkt = wkb.dumps(geom, hex=True, srid=3005)

        timestamp = datetime.now()

        # commit to db
        op.execute(thessian_polygon_area.insert(values={'station_code': station_code, 'geom': wkt, 'create_date': timestamp, 'update_date': timestamp}))

        feature = layer.GetNextFeature()


def downgrade():
    op.execute('DELETE FROM thessian_polygon_area')
