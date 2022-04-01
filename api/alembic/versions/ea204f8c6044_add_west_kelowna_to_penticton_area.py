"""add west kelowna to Penticton area

Revision ID: ea204f8c6044
Revises: c525dbd0c37e
Create Date: 2022-04-01 11:38:13.822949

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ea204f8c6044'
down_revision = 'c525dbd0c37e'
branch_labels = None
depends_on = None


def get_fuel_type_id(fuel_type):
    # Helper function to get fuel_types.id
    conn = op.get_bind()
    cursor = conn.execute(f"SELECT id FROM fuel_types WHERE abbrev = '{fuel_type}'")
    result = cursor.fetchall()
    return result[0][0]


def get_kamloops_fire_centre_id():
    conn = op.get_bind()
    res = conn.execute('SELECT id FROM fire_centres WHERE name LIKE \'Kamloops Fire Centre\'')
    return int(str(res.fetchall()[0]).replace('(', '').replace(',', '').replace(')', ''))


def get_penticton_planning_area_id(kamloops_fc_id):
    conn = op.get_bind()
    res = conn.execute(
        "SELECT id FROM planning_areas WHERE fire_centre_id = {} AND name LIKE \'Penticton%%\'".format(kamloops_fc_id))
    return int(str(res.fetchall()[0]).replace('(', '').replace(',', '').replace(')', ''))


def delete_all_stations_in_planning_area_id(planning_area_id):
    op.execute(f"DELETE FROM planning_weather_stations WHERE planning_area_id = {planning_area_id}")


def insert_stations_for_planning_area(new_stations):
    for station in new_stations:
        op.execute(
            f"INSERT INTO planning_weather_stations (station_code, fuel_type_id, planning_area_id,\
                order_of_appearance_in_planning_area_list) VALUES ({station[0]}, {station[1]},\
                    {station[2]}, {station[3]})")


def upgrade():
    kfc_id = get_kamloops_fire_centre_id()
    penticton_id = get_penticton_planning_area_id(kfc_id)

    # First remove all existing planning weather stations in Penticton area
    delete_all_stations_in_planning_area_id(penticton_id)

    c7_id = get_fuel_type_id('C7')
    c7b_id = get_fuel_type_id('C7B')

    new_penticton_stations = [
        [328, c7b_id, penticton_id, 1],
        [1227, c7_id, penticton_id, 2],
        [334, c7b_id, penticton_id, 3]
    ]

    insert_stations_for_planning_area(new_penticton_stations)


def downgrade():
    kfc_id = get_kamloops_fire_centre_id()
    penticton_id = get_penticton_planning_area_id(kfc_id)
    c7b_id = get_fuel_type_id('C7B')

    old_penticton_stations = [
        [328, c7b_id, penticton_id, 1],
        [334, c7b_id, penticton_id, 2]
    ]

    # First remove all existing planning weather stations in Penticton area
    delete_all_stations_in_planning_area_id(penticton_id)

    insert_stations_for_planning_area(old_penticton_stations)
