"""Import remaining fire centres, planning areas, etc. for HFI calc

Revision ID: 8efe0e7b9712
Revises: 1caf3488a340
Create Date: 2022-01-13 17:18:52.430766

"""
import json
from alembic import op


# revision identifiers, used by Alembic.
revision = '8efe0e7b9712'
down_revision = '1caf3488a340'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Migration to import remaining data from updated planning_areas.json
    # performs same operation as in initial_hfi_data_import.py except ignores conflicts
    # so that there's no duplicate entries

    # Load planning areas data
    with open('app/data/planning_areas.json') as planning_areas_file:
        planning_areas_data = json.load(planning_areas_file)

    # populate fire_centres table with all fire centres from planning_areas_file that don't already exist in database
    fire_centres = planning_areas_data['fire_centres']
    for centre in fire_centres:
        for key, values in centre.items():
            fire_centre_name = '\'' + key + '\''

            op.execute('INSERT INTO fire_centres (name) VALUES ({}) ON CONFLICT (name) DO NOTHING'.format(
                fire_centre_name))

            # for each zone (planning area), need to get the fire centre id based on the fire centre name
            # insert into planning_areas table list of zone_name-fire_centre_id pairs
            for zone_dict in values['zones']:
                zone_name = '\'' + list(zone_dict.keys())[0] + '\''
                res = conn.execute('SELECT id FROM fire_centres WHERE name LIKE {}'.format(fire_centre_name))
                results = res.fetchall()
                fire_centre_id = str(results[0]).replace('(', '').replace(')', '').replace(',', '')
                op.execute('INSERT INTO planning_areas (name, fire_centre_id) VALUES ({}, {}) ON CONFLICT (name, fire_centre_id) DO NOTHING'.format(
                    zone_name, fire_centre_id))

                stations = list(zone_dict.values())[0].get('stations')[0]
                for station_code, fuel_type_dict in stations.items():
                    station_code = int(station_code)
                    fuel_type_abbrev = '\'' + fuel_type_dict['fuel_type'] + '\''
                    fuel_type_query = conn.execute(
                        'SELECT id FROM fuel_types WHERE abbrev LIKE {}'.format(fuel_type_abbrev))
                    fuel_type_results = fuel_type_query.fetchall()
                    fuel_type_id = str(fuel_type_results[0]).replace(
                        '(', '').replace(')', '').replace(',', '')
                    planning_area_query = conn.execute(
                        'SELECT id FROM planning_areas WHERE name LIKE {}'.format(zone_name))
                    planning_area_results = planning_area_query.fetchall()
                    planning_area_id = str(planning_area_results[0]).replace(
                        '(', '').replace(')', '').replace(',', '')
                    op.execute('INSERT INTO planning_weather_stations (station_code, fuel_type_id, '
                               'planning_area_id) VALUES ({}, {}, {}) ON CONFLICT (station_code, fuel_type_id, planning_area_id) DO NOTHING'.format(
                                   station_code, fuel_type_id, planning_area_id))


def downgrade():
    # deletes all entries in planning_weather_stations, planning_areas, and fire_centres EXCEPT for
    # those pertaining to Kamloops Fire Centre - those were added in a previous migration (1caf3488a340)
    # I don't like this approach but I can't think of a better way to do it
    op.execute('DELETE FROM planning_weather_stations WHERE planning_area_id > 5 ')
    op.execute('DELETE FROM planning_areas WHERE fire_centre_id > 1')
    op.execute('DELETE FROM fire_centres WHERE id > 1')
