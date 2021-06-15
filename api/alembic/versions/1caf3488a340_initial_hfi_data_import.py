"""Initial HFI data import

Revision ID: 1caf3488a340
Revises: 43dce8db9afb
Create Date: 2021-06-01 15:51:27.767517

"""
import json
from alembic import op

# revision identifiers, used by Alembic.
revision = '1caf3488a340'
down_revision = '43dce8db9afb'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Load fuel types data
    with open('app/data/fuel_types.json') as fuel_types_file:
        fuel_types_data = json.load(fuel_types_file)

    for fuel_type in fuel_types_data['fuel_types']:
        abbrev_data = '\'' + fuel_type.get('abbrev') + '\''
        description_data = '\'' + fuel_type.get('description') + '\''
        op.execute('INSERT INTO fuel_types (abbrev, description) VALUES ({}, {})'.format(
            abbrev_data, description_data))

    # Load planning areas data
    with open('app/data/planning_areas.json') as planning_areas_file:
        planning_areas_data = json.load(planning_areas_file)

    # populate fire_centres table
    fire_centres = planning_areas_data['fire_centres']
    for centre in fire_centres:
        for key, values in centre.items():
            fire_centre_name = '\'' + key + '\''
            op.execute('INSERT INTO fire_centres (name) VALUES ({})'.format(fire_centre_name))

            # for each zone (planning area), need to get the fire centre id based on the fire centre name
            # insert into planning_areas table list of zone_name-fire_centre_id pairs
            for zone_dict in values['zones']:
                zone_name = '\'' + list(zone_dict.keys())[0] + '\''
                res = conn.execute('SELECT id FROM fire_centres WHERE name LIKE {}'.format(fire_centre_name))
                results = res.fetchall()
                fire_centre_id = str(results[0]).replace('(', '').replace(')', '').replace(',', '')
                op.execute('INSERT INTO planning_areas (name, fire_centre_id) VALUES ({}, {})'.format(
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
                               'planning_area_id) VALUES ({}, {}, {})'.format(
                                   station_code, fuel_type_id, planning_area_id))


def downgrade():
    op.execute('DELETE FROM planning_weather_stations')
    op.execute('DELETE FROM planning_areas')
    op.execute('DELETE FROM fire_centres')
    op.execute('DELETE FROM fuel_types')
