""" Routers for HFI Calculator """
import logging
import math
from typing import List, Optional
from aiohttp.client import ClientSession
from fastapi import APIRouter, Response, Depends, Query
from app.wildfire_one import (get_wfwx_stations_from_station_codes,
                              get_dailies,
                              get_auth_header)
from app.utils.time import get_utc_today_start_and_end
from app.schemas.hfi_calc import StationDailyResponse
import app
from app import wildfire_one
from app.auth import authentication_required, audit
from app.schemas.hfi_calc import (HFIWeatherStationsResponse, WeatherStationProperties,
                                  FuelType, FireCentre, PlanningArea, WeatherStation)
from app.db.crud.hfi_calc import get_fire_weather_stations


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/hfi-calc",
    dependencies=[Depends(authentication_required), Depends(audit)]
)


def validate_time_range(start_time_stamp: Optional[int], end_time_stamp: Optional[int]):
    """ Sets timestamp to today if they are None.
        Defaults to start of today and end of today if no range is given. """
    if start_time_stamp is None or end_time_stamp is None:
        today_start, today_end = get_utc_today_start_and_end()
        return math.floor(today_start.timestamp()*1000), math.floor(today_end.timestamp()*1000)
    return int(start_time_stamp), int(end_time_stamp)


@router.get('/daily', response_model=StationDailyResponse)
async def get_daily_view(response: Response,
                         _=Depends(authentication_required),
                         station_codes: Optional[List[int]] = Query(None),
                         start_time_stamp: Optional[int] = None,
                         end_time_stamp: Optional[int] = None):
    """ Returns daily metrics for each station code. """
    logger.info('/hfi-calc/daily')
    response.headers["Cache-Control"] = "max-age=0"  # don't let the browser cache this
    valid_start_time, valid_end_time = validate_time_range(start_time_stamp, end_time_stamp)

    async with ClientSession() as session:
        header = await get_auth_header(session)
        # Get the stations (using cache if possible)
        wfwx_stations = await get_wfwx_stations_from_station_codes(session,
                                                                   header,
                                                                   station_codes,
                                                                   use_cache=True)
        dailies = await get_dailies(
            session, header, wfwx_stations, valid_start_time, valid_end_time)
        return StationDailyResponse(dailies=dailies)


@router.get('/fire-centres', response_model=HFIWeatherStationsResponse)
async def get_fire_centres(response: Response):  # pylint: disable=too-many-locals
    """ Returns list of fire centres and planning area for each fire centre,
    and weather stations within each planning area. Also returns the assigned fuel type
    for each weather station. """
    try:
        logger.info('/hfi-calc/fire-centres')
        response.headers["Cache-Control"] = "max-age=0"  # don't let the browser cache this

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
                        description=fuel_type_record.description),
                    'planning_area': planning_area_record,
                    'fire_centre': fire_centre_record
                }

                if fire_centres_dict.get(fire_centre_record.name) is None:
                    fire_centres_dict[fire_centre_record.name] = {
                        'fire_centre_record': fire_centre_record,
                        'planning_area_records': [planning_area_record],
                        'planning_area_objects': []
                    }
                else:
                    fire_centres_dict.get(fire_centre_record.name)[
                        'planning_area_records'].append(planning_area_record)
                    fire_centres_dict[fire_centre_record.name]['planning_area_records'] = list(
                        set(fire_centres_dict.get(fire_centre_record.name).get('planning_area_records')))

                if planning_areas_dict.get(planning_area_record.name) is None:
                    planning_areas_dict[planning_area_record.name] = {
                        'planning_area_record': planning_area_record,
                        'station_codes': [station_record.station_code],
                        'station_objects': []
                    }
                else:
                    planning_areas_dict[planning_area_record.name]['station_codes'].append(
                        station_record.station_code)

            # We're still missing some data that we need from wfwx, so give it the list of stations
            wfwx_stations_data = await wildfire_one.get_stations_by_codes(list(station_info_dict.keys()))
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
                                                 station_props=station_properties)

                station_info_dict[wfwx_station.code]['station'] = weather_station

                planning_areas_dict[station_info_dict[wfwx_station.code]
                                    ['planning_area'].name]['station_objects'].append(weather_station)

        # create PlanningArea objects containing all corresponding WeatherStation objects
        for key, val in planning_areas_dict.items():
            planning_area = PlanningArea(name=key, stations=val['station_objects'])
            planning_areas_dict[key]['planning_area_object'] = planning_area

        # create FireCentre objects containing all corresponding PlanningArea objects
        for key, val in fire_centres_dict.items():
            planning_area_objects_list = []
            for pa_record in val['planning_area_records']:
                pa_object = planning_areas_dict.get(pa_record.name).get('planning_area_object')
                planning_area_objects_list.append(pa_object)
            fire_centre = FireCentre(name=key, planning_areas=planning_area_objects_list)
            fire_centres_list.append(fire_centre)

        return HFIWeatherStationsResponse(fire_centres=fire_centres_list)

    except Exception as exc:
        logger.critical(exc, exc_info=True)
        raise


def get_wfwx_station(wfwx_stations_data: List[WeatherStation], station_code: int):
    """ Helper function to find station corresponding to station_code from the list of
    weather stations returned from WFWX. """
    for station in wfwx_stations_data:
        if station.code == station_code:
            return station
    return None
