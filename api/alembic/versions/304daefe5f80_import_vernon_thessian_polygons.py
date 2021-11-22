"""Import vernon thessian polygons

Revision ID: 304daefe5f80
Revises: 11b821827824
Create Date: 2021-11-22 11:30:18.090021

"""
from alembic import op
import os


# revision identifiers, used by Alembic.
revision = '304daefe5f80'
down_revision = '11b821827824'
branch_labels = None
depends_on = None


file_path = os.getcwd() + '/alembic/vernon_area_prototype/VernonFZBATPolys.shp'
command = f'ogr2ogr -f "PostgreSQL" PG:"dbname=wps user=postgres" "{file_path}" -nln fire_area_thessian_polygons -append'


def upgrade():
    os.system(command)


def downgrade():
    op.execute('DELETE FROM fire_area_thessian_polygons')
