"""Import remaining fire centres, planning areas, etc. for HFI calc

Revision ID: 8efe0e7b9712
Revises: 39806f02cdec
Create Date: 2022-01-13 17:18:52.430766

"""
import json
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '8efe0e7b9712'
down_revision = '39806f02cdec'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Due to confusing Alembic revision conflicts, some databases will have this constraint at this revision and
    # others won't. Delete the constraint if it exists - it's not applicable anymore.
    op.execute('ALTER TABLE planning_weather_stations DROP CONSTRAINT IF EXISTS planning_weather_stations_station_code_key')

    # Migration to import remaining data from 8efe0e7b9712_add_remaining_fcs_for_hfi.json
    # performs same operation as in initial_hfi_data_import.py

    # Load planning areas data
    with open('alembic/versions/8efe0e7b9712_add_remaining_fcs_for_hfi.json') as planning_areas_file:
        planning_areas_data = json.load(planning_areas_file)

    # populate fire_centres table with all fire centres from planning_areas_file that don't already exist in database
    fire_centres = planning_areas_data['fire_centres']
    for centre in fire_centres:
        for key, values in centre.items():
            fire_centre_name = '\'' + key + '\''

            op.execute('INSERT INTO fire_centres (name) VALUES ({})'.format(
                fire_centre_name))

            # for each zone (planning area), need to get the fire centre id based on the fire centre name
            # insert into planning_areas table list of zone_name-fire_centre_id pairs
            for zone_dict in values['zones']:
                zone_name = '\'' + list(zone_dict.keys())[0] + '\''
                res = conn.execute(text('SELECT id FROM fire_centres WHERE name LIKE {}'.format(fire_centre_name)))
                results = res.fetchall()
                fire_centre_id = str(results[0]).replace('(', '').replace(')', '').replace(',', '')
                op.execute('INSERT INTO planning_areas (name, fire_centre_id) VALUES ({}, {})'.format(
                    zone_name, fire_centre_id))

                stations = list(zone_dict.values())[0].get('stations')[0]
                for station_code, fuel_type_dict in stations.items():
                    station_code = int(station_code)
                    fuel_type_abbrev = '\'' + fuel_type_dict['fuel_type'] + '\''
                    fuel_type_query = conn.execute(
                        text('SELECT id FROM fuel_types WHERE abbrev LIKE {}'.format(fuel_type_abbrev)))
                    fuel_type_results = fuel_type_query.fetchall()
                    fuel_type_id = str(fuel_type_results[0]).replace(
                        '(', '').replace(')', '').replace(',', '')
                    planning_area_query = conn.execute(
                        text('SELECT id FROM planning_areas WHERE name LIKE {}'.format(zone_name)))
                    planning_area_results = planning_area_query.fetchall()
                    planning_area_id = str(planning_area_results[0]).replace(
                        '(', '').replace(')', '').replace(',', '')
                    op.execute('INSERT INTO planning_weather_stations (station_code, fuel_type_id, '
                               'planning_area_id) VALUES ({}, {}, {})'.format(
                                   station_code, fuel_type_id, planning_area_id))


def downgrade():
    # deletes all entries in planning_weather_stations, planning_areas, and fire_centres EXCEPT for
    # those pertaining to Kamloops Fire Centre - those were added in a previous migration (1caf3488a340)
    # I don't like this approach but I can't think of a better way to do it
    conn = op.get_bind()

    kamloops_fire_centre_id_query = conn.execute(
        'SELECT id FROM fire_centres WHERE name like \'Kamloops Fire Centre\'')
    kamloops_fire_centre_id = str(kamloops_fire_centre_id_query.fetchall()[0]).replace(
        '(', '').replace(')', '').replace(',', '')
    kamloops_planning_area_ids_query = conn.execute(
        'SELECT id FROM planning_areas WHERE fire_centre_id = {}'.format(kamloops_fire_centre_id))
    kamloops_planning_area_ids = kamloops_planning_area_ids_query.fetchall()
    kamloops_planning_area_ids = str(kamloops_planning_area_ids).replace(
        '[', '').replace(']', '').replace("(", "").replace(")", "").replace(',,', ',')
    kamloops_planning_area_ids = '(' + kamloops_planning_area_ids[:-1] + ')'
    print(kamloops_planning_area_ids)
    op.execute('DELETE FROM planning_weather_stations WHERE planning_area_id NOT IN {}'.format(
        kamloops_planning_area_ids))
    op.execute('DELETE FROM planning_areas WHERE id NOT IN {}'.format(
        kamloops_planning_area_ids))
    op.execute('DELETE FROM fire_centres WHERE id != {}'.format(kamloops_fire_centre_id))
