"""Remove Bear Lake station from planning_area_stations
for Prince George Fire Centre. 
Bear Lake station (code 149) no longer exists in WFWX and is causing problems in prod.

Revision ID: ac65354014bd
Revises: 16386a52d7bf
Create Date: 2022-05-12 12:31:45.944743

"""
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'ac65354014bd'
down_revision = '16386a52d7bf'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('DELETE FROM planning_weather_stations WHERE station_code = 149')


def downgrade():
    conn = op.get_bind()

    # default fuel type for Bear Lake is C3
    res = conn.execute(text('SELECT id FROM fuel_types WHERE abbrev LIKE \'C3\''))
    results = res.fetchall()
    fuel_type_id = str(results[0]).replace('(', '').replace(',', '').replace(')', '')

    # fire centre is Prince George FC, planning area is Prince George Zone
    res = conn.execute(text('SELECT id FROM planning_areas WHERE name LIKE {}'.format('\'Prince George Zone%%\'')))
    results = res.fetchall()
    planning_area_id = results[0][0]

    # order_of_appearance_in_planning_area_list is 4
    op.execute(
        'INSERT INTO planning_weather_stations (station_code, fuel_type_id, planning_area_id, order_of_appearance_in_planning_area_list) VALUES (149, {}, {}, 4)'.format(fuel_type_id, planning_area_id))
