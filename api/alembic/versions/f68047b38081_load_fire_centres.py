"""load_fire_centres

Revision ID: f68047b38081
Revises: d6e9a814aa6f
Create Date: 2021-01-25 16:27:01.445046

"""
import os
import json
from alembic import op
from sqlalchemy import String
from sqlalchemy.sql import table, column
from geoalchemy2 import Geometry
from shapely.geometry import shape


# revision identifiers, used by Alembic.
revision = 'f68047b38081'
down_revision = 'd6e9a814aa6f'
branch_labels = None
depends_on = None


def upgrade():
    """ Insert fire centre geometries into database """
    prediction_models = table('fire_centers',
                              column('name', String), column('geom', Geometry))
    filename = os.path.join(os.path.dirname(__file__), './geojson/DRP_MOF_FIRE_CENTRES_SP.geojson')
    with open(filename) as json_fp:
        data = json.load(json_fp)
        for feature in data['features']:
            geom = shape(feature['geometry'])
            name = feature['properties']['MOF_FIRE_CENTRE_NAME']
            op.execute(prediction_models.insert().values({'name': name, 'geom': geom.wkt}))


def downgrade():
    """ Delete the fire centers """
    op.execute('DELETE FROM fire_centers')
