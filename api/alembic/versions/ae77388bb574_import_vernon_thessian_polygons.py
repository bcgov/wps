"""Import vernon thessian polygons

Revision ID: ae77388bb574
Revises: 2ca7085c412b
Create Date: 2021-11-22 13:48:10.405804

"""
from alembic import op
import sqlalchemy as sa
import os


# revision identifiers, used by Alembic.
revision = 'ae77388bb574'
down_revision = '2ca7085c412b'
branch_labels = None
depends_on = None


file_path = os.getcwd() + '/alembic/vernon_area_prototype/VernonFZBATPolys.shp'
command = f'ogr2ogr -f "PostgreSQL" PG:"dbname=wps user=postgres" "{file_path}" -nln fire_area_thessian_polygons -append'


def upgrade():
    os.system(command)


def downgrade():
    op.execute('DELETE FROM thessian_polygon_area')
