"""Add Haida Gwaii zone to COFC

Revision ID: 2169aa76dfea
Revises: e201ae32516e
Create Date: 2023-04-20 11:42:45.140495

"""
from alembic import op
import sqlalchemy as sa

from app.utils.time import get_utc_now


# revision identifiers, used by Alembic.
revision = '2169aa76dfea'
down_revision = 'e201ae32516e'
branch_labels = None
depends_on = None

# ------ HELPER FUNCTIONS -----------


def get_fire_centre_id(conn, name: str):
    res = conn.execute(sa.text('SELECT id FROM fire_centres WHERE name = \'{}\''.format(name)))
    results = res.fetchall()
    return results[0][0]


def get_zone(conn, name: str, fire_centre_id: int):
    res = conn.execute(
        sa.text('SELECT * FROM planning_areas WHERE name = \'{}\' AND fire_centre_id = {}'.format(name, fire_centre_id)))
    results = res.fetchall()
    return results[0]


def get_planning_weather_station(conn, station_code: int, planning_area_id: int):
    res = conn.execute(sa.text(
        'SELECT * FROM planning_weather_stations WHERE station_code = {} and planning_area_id = {}'.format(station_code, planning_area_id)))
    results = res.fetchall()
    return results[0]


def get_fuel_type_id(conn, fuel_type_abbrev: str):
    res = conn.execute(sa.text('SELECT id FROM fuel_types WHERE abbrev = \'{}\''.format(fuel_type_abbrev)))
    results = res.fetchall()
    return results[0][0]


def increase_value_order_of_appearance(conn, fire_centre_id: int, from_index: int):
    # due to constraint on unique value of (fire_centre_id, order_of_appearance_in_list), have to
    # modify values of order_of_appearance_in_list one at a time, otherwise error is thrown
    res = conn.execute(
        sa.text('SELECT MAX(order_of_appearance_in_list) FROM planning_areas WHERE fire_centre_id = {}'.format(fire_centre_id)))
    max_value_order = res.fetchall()[0][0]
    index = max_value_order
    while index > from_index:
        conn.execute(sa.text('UPDATE planning_areas SET order_of_appearance_in_list = order_of_appearance_in_list + 1 WHERE fire_centre_id = {} AND order_of_appearance_in_list = {}'.format(fire_centre_id, index)))
        index -= 1


def decrease_value_order_of_appearance(conn, fire_centre_id: int, to_index: int):
    # due to constraint on unique value of (fire_centre_id, order_of_appearance_in_list), have to
    # modify values of order_of_appearance_in_list one at a time, otherwise error is thrown
    res = conn.execute(
        sa.text('SELECT MAX(order_of_appearance_in_list) FROM planning_areas WHERE fire_centre_id = {}'.format(fire_centre_id)))
    max_value_order = res.fetchall()[0][0]
    index = to_index
    while index <= max_value_order:
        conn.execute(sa.text('UPDATE planning_areas SET order_of_appearance_in_list = order_of_appearance_in_list - 1 WHERE fire_centre_id = {} AND order_of_appearance_in_list = {}'.format(fire_centre_id, index)))
        index += 1

# ------ end of helper functions ----


def upgrade():
    conn = op.get_bind()

    cofc_id = get_fire_centre_id(conn, 'Coastal Fire Centre')
    fraser_zone = get_zone(conn, 'Fraser Zone', cofc_id)
    fraser_zone_id = fraser_zone[0]
    m2_25_id = get_fuel_type_id(conn, 'M2 25%')

    print(cofc_id, fraser_zone_id, m2_25_id)

    # 1. Increase order_of_appearance_in_list by 1 for all planning areas in COFC with order value > 1
    increase_value_order_of_appearance(conn, cofc_id, 1)

    # 2. Add Haida Gwaii planning area for COFC with order_of_appearance_in_list = 2
    conn.execute(sa.text(
        'INSERT INTO planning_areas (name, fire_centre_id, order_of_appearance_in_list) VALUES (\'Haida Gwaii\', {}, 2)'.format(cofc_id)))

    # 3. Add Honna station (station code 93) to Haida Gwaii planning area
    haida_gwaii_zone = get_zone(conn, 'Haida Gwaii', cofc_id)
    haida_gwaii_zone_id = haida_gwaii_zone[0]
    now = get_utc_now()
    conn.execute(sa.text(
        'INSERT INTO planning_weather_stations (station_code, fuel_type_id, planning_area_id, order_of_appearance_in_planning_area_list, create_user, create_timestamp, update_user, update_timestamp, is_deleted) VALUES (93, {}, {}, 1, \'system\', \'{}\', \'system\', \'{}\', false)'.format(m2_25_id, haida_gwaii_zone_id, now, now)))

    # 4. Remove Honna station from Fraser zone in COFC
    honna_fraser = get_planning_weather_station(conn, 93, fraser_zone_id)
    print(honna_fraser)
    conn.execute(sa.text(
        'DELETE FROM planning_weather_stations WHERE station_code = 93 AND planning_area_id = {}'.format(fraser_zone_id)))


def downgrade():
    conn = op.get_bind()

    cofc_id = get_fire_centre_id(conn, 'Coastal Fire Centre')
    fraser_zone = get_zone(conn, 'Fraser Zone', cofc_id)
    fraser_zone_id = fraser_zone[0]
    haida_gwaii_zone = get_zone(conn, 'Haida Gwaii', cofc_id)
    haida_gwaii_zone_id = haida_gwaii_zone[0]
    m2_25_id = get_fuel_type_id(conn, 'M2 25%')

    # 1. Add Honna station to Fraser zone in COFC
    now = get_utc_now()
    conn.execute(sa.text('INSERT INTO planning_weather_stations (station_code, fuel_type_id, planning_area_id, order_of_appearance_in_planning_area_list, create_user, create_timestamp, update_user, update_timestamp, is_deleted) VALUES (93, {}, {}, 5, \'system\', \'{}\', \'system\', \'{}\', false)'.format(m2_25_id, fraser_zone_id, now, now)))

    # 2. Delete Honna station from Haida Gwaii planning area
    honna_haida_gwaii = get_planning_weather_station(conn, 93, haida_gwaii_zone_id)
    conn.execute(sa.text('DELETE FROM planning_weather_stations WHERE station_code = {} AND planning_area_id = {}'.format(
        honna_haida_gwaii[1], haida_gwaii_zone_id)))

    # 3. Delete Haida Gwaii planning area for COFC
    conn.execute(sa.text('DELETE FROM planning_areas WHERE id = {}'.format(haida_gwaii_zone_id)))

    # 4. Decrease values of order_of_appearance_in_list by 1 for all planning areas in COFC with order value > 2
    decrease_value_order_of_appearance(conn, cofc_id, 2)
