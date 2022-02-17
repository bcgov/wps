"""Import revised HFI calc data

Revision ID: 9a5bb047ae19
Revises: fb9d656fdc19
Create Date: 2022-02-09 11:14:13.773005

"""
from alembic import op
import json


# revision identifiers, used by Alembic.
revision = '9a5bb047ae19'
down_revision = 'fb9d656fdc19'
branch_labels = None
depends_on = None


def get_fuel_type_id(fuel_type):
    # Helper function to get fuel_types.id
    conn = op.get_bind()
    if fuel_type == 'M2_25':
        cursor = conn.execute(f"SELECT id FROM fuel_types WHERE abbrev = 'M2' AND percentage_conifer = 25")
    else:
        cursor = conn.execute(f"SELECT id FROM fuel_types WHERE abbrev = '{fuel_type}'")
    result = cursor.fetchall()
    return result[0][0]

def upgrade():
    conn = op.get_bind()

    # Load stations data
    with open('alembic/versions/9a5bb047ae19_import_revised_hfi_calc_data.json') as stations_data_file:
        stations_data = json.load(stations_data_file)

    # First delete all data from planning_areas and planning_weather_stations - going to overwrite it
    # with updated data
    op.execute('DELETE FROM planning_weather_stations')
    op.execute('DELETE FROM planning_areas')

    # populate fire_centres table with all fire centres from stations_data_file
    fire_centres = stations_data['fire_centres']
    for centre in fire_centres:
        for key, values in centre.items():
            fire_centre_name = '\'' + key + '\''
            res = conn.execute(f"SELECT id FROM fire_centres WHERE name LIKE {fire_centre_name}")
            fire_centre_id = res.fetchall()[0][0]

            for area in values['zones']:
                for pa_key in area:
                    planning_area_name = '\'' + pa_key + '\''
                    order = area[pa_key]['order_of_appearance_in_list']

                    op.execute(f"INSERT INTO planning_areas (name, fire_centre_id, order_of_appearance_in_list)\
                        VALUES ({planning_area_name}, {fire_centre_id}, {order})")
                    result = conn.execute(f"SELECT id FROM planning_areas WHERE name LIKE {planning_area_name}")
                    planning_area_id = result.fetchall()[0][0]

                    for station in area[pa_key]['stations']:
                        for station_code in station:
                            station_fuel_type = station[station_code]['fuel_type']
                            fuel_type_id = get_fuel_type_id(station_fuel_type)
                            station_order = station[station_code]['order_of_appearance_in_planning_area_list']
                            op.execute(f"INSERT INTO planning_weather_stations (station_code, fuel_type_id,\
                                planning_area_id, order_of_appearance_in_planning_area_list) VALUES\
                                ({station_code}, {fuel_type_id}, {planning_area_id}, {station_order})")
                    


def downgrade():
    # There's no easy way to revert data changes - just delete all data in planning_weather_stations and planning_areas
    op.execute("DELETE FROM planning_weather_stations")
    op.execute("DELETE FROM planning_areas")
