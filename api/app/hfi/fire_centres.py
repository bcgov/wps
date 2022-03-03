""" Fire centre data logic """
import app
from app.schemas.hfi_calc import (WeatherStationProperties,
                                  FuelType, FireCentre, PlanningArea, WeatherStation)
from app.wildfire_one.wfwx_api import get_stations_by_codes
from app.db.crud.hfi_calc import get_fire_weather_stations


async def get_hydrated_fire_centres():
    """ Merges all fire centre data from WPS and WFWX sources """
    with app.db.database.get_read_session_scope() as session:
        # Fetch all fire weather stations from the database.
        station_query = get_fire_weather_stations(session)
        # Prepare a dictionary for storing station info in.
        station_info_dict = {}
        # Prepare empty data structures to be used in HFIWeatherStationsResponse
        fire_centres_list = []
        planning_areas_dict = {}
        fire_centres_dict = {}

        # Iterate through all the database records, collecting all the data we need.
        for (station_record, fuel_type_record, planning_area_record, fire_centre_record) in station_query:
            station_info_dict[station_record.station_code] = {
                'fuel_type': FuelType(
                    abbrev=fuel_type_record.abbrev,
                    fuel_type_code=fuel_type_record.fuel_type_code,
                    description=fuel_type_record.description,
                    percentage_conifer=fuel_type_record.percentage_conifer,
                    percentage_dead_fir=fuel_type_record.percentage_dead_fir),
                # pylint: disable=line-too-long
                'order_of_appearance_in_planning_area_list': station_record.order_of_appearance_in_planning_area_list,
                'planning_area': planning_area_record,
                'fire_centre': fire_centre_record
            }

            if fire_centres_dict.get(fire_centre_record.id) is None:
                fire_centres_dict[fire_centre_record.id] = {
                    'fire_centre_record': fire_centre_record,
                    'planning_area_records': [planning_area_record],
                    'planning_area_objects': []
                }
            else:
                fire_centres_dict.get(fire_centre_record.id)[
                    'planning_area_records'].append(planning_area_record)
                fire_centres_dict[fire_centre_record.id]['planning_area_records'] = list(
                    set(fire_centres_dict.get(fire_centre_record.id).get('planning_area_records')))

            if planning_areas_dict.get(planning_area_record.id) is None:
                planning_areas_dict[planning_area_record.id] = {
                    'planning_area_record': planning_area_record,
                    'order_of_appearance_in_list': planning_area_record.order_of_appearance_in_list,
                    'station_codes': [station_record.station_code],
                    'station_objects': []
                }
            else:
                planning_areas_dict[planning_area_record.id]['station_codes'].append(
                    station_record.station_code)

        # We're still missing some data that we need from wfwx, so give it the list of stations
        wfwx_stations_data = await get_stations_by_codes(list(station_info_dict.keys()))
        # Iterate through all the stations from wildfire one.

        for wfwx_station in wfwx_stations_data:
            station_info = station_info_dict[wfwx_station.code]
            # Combine everything.
            station_properties = WeatherStationProperties(
                name=wfwx_station.name,
                fuel_type=station_info['fuel_type'],
                elevation=wfwx_station.elevation,
                wfwx_station_uuid=wfwx_station.wfwx_station_uuid)

            weather_station = WeatherStation(code=wfwx_station.code,
                                             order_of_appearance_in_planning_area_list=station_info[
                                                 'order_of_appearance_in_planning_area_list'],
                                             station_props=station_properties)

            station_info_dict[wfwx_station.code]['station'] = weather_station

            planning_areas_dict[station_info_dict[wfwx_station.code]
                                ['planning_area'].id]['station_objects'].append(weather_station)

    # create PlanningArea objects containing all corresponding WeatherStation objects
    for key, val in planning_areas_dict.items():
        planning_area = PlanningArea(
            id=val['planning_area_record'].id,
            name=val['planning_area_record'].name,
            order_of_appearance_in_list=val['order_of_appearance_in_list'],
            stations=val['station_objects'])
        val['planning_area_object'] = planning_area

    # create FireCentre objects containing all corresponding PlanningArea objects
    for key, val in fire_centres_dict.items():
        planning_area_objects_list = []
        for pa_record in val['planning_area_records']:
            pa_object = planning_areas_dict.get(pa_record.id).get('planning_area_object')
            planning_area_objects_list.append(pa_object)
        fire_centre = FireCentre(
            id=key, name=val['fire_centre_record'].name, planning_areas=planning_area_objects_list)
        fire_centres_list.append(fire_centre)

    return fire_centres_list
