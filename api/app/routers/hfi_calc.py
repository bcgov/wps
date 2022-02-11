""" Routers for HFI Calculator """
import logging
import math
from typing import List, Optional
from aiohttp.client import ClientSession
from fastapi import APIRouter, Response, Depends, Query
from app.hfi.hfi import calculate_hfi_results
import app.utils.time
from app.schemas.hfi_calc import HFIResultRequest, HFIResultResponse, StationDailyResponse
import app
from app.auth import authentication_required, audit
from app.schemas.hfi_calc import (HFIWeatherStationsResponse, WeatherStationProperties,
                                  FuelType, FireCentre, PlanningArea, WeatherStation)
from app.db.crud.hfi_calc import get_fire_weather_stations, get_most_recent_updated_hfi_request, store_hfi_request
from app.wildfire_one.wfwx_api import (get_auth_header,
                                       get_dailies_lookup_fuel_types,
                                       get_stations_by_codes)


logger = logging.getLogger(__name__)

no_cache = "max-age=0"  # don't let the browser cache this

router = APIRouter(
    prefix="/hfi-calc",
    dependencies=[Depends(authentication_required), Depends(audit)]
)


def load_request(request: HFIResultRequest) -> HFIResultRequest:
    """ If we need to load the request from the database, we do so. Otherwise we return the request as is. """
    if request.start_time_stamp is None:
        with app.db.database.get_read_session_scope() as session:
            stored_request = get_most_recent_updated_hfi_request(session, request.selected_fire_center)
            if stored_request:
                return HFIResultRequest.from_dict(stored_request.request)
    return request


def save_request(request: HFIResultRequest, username: str):
    if request.start_time_stamp is not None and request.end_time_stamp is not None:
        with app.db.database.get_write_session_scope() as session:
            store_hfi_request(session, request, username)
    return request


@router.post('/', response_model=HFIResultResponse)
async def get_hfi_results(request: HFIResultRequest,
                          response: Response,
                          token=Depends(authentication_required)):
    """ Returns calculated HFI results for the supplied details in the POST body """

    try:
        logger.info('/hfi-calc/')
        response.headers["Cache-Control"] = no_cache

        request = load_request(request)

        valid_start_time, valid_end_time = validate_time_range(
            request.start_time_stamp, request.end_time_stamp)

        async with ClientSession() as session:
            header = await get_auth_header(session)
            wfwx_stations = await app.wildfire_one.wfwx_api.get_wfwx_stations_from_station_codes(
                session, header, request.selected_station_codes)
            dailies = await get_dailies_lookup_fuel_types(
                session, header, wfwx_stations, valid_start_time, valid_end_time)
            results = calculate_hfi_results(request.selected_fire_center,
                                            request.planning_area_fire_starts,
                                            dailies, request.num_prep_days,
                                            request.selected_station_codes)
        response = HFIResultResponse(
            num_prep_days=request.num_prep_days,
            selected_prep_date=request.selected_prep_date,
            start_time_stamp=valid_start_time,
            end_time_stamp=valid_end_time,
            selected_station_codes=request.selected_station_codes,
            selected_fire_center=request.selected_fire_center,
            planning_area_hfi_results=results,
            planning_area_fire_starts=request.planning_area_fire_starts)

        # NOTE: we want to delay saving the request as much as possible - if the request breaks the response,
        # we don't want to save it!
        # TODO: add check for "save" button
        save_request(request, token.get('preferred_username', None))

        return response
    except Exception as exc:
        logger.critical(exc, exc_info=True)
        raise


def validate_time_range(start_time_stamp: Optional[int], end_time_stamp: Optional[int]):
    """ Sets timestamp to today if they are None.
        Defaults to start of today and end of today if no range is given. """
    if start_time_stamp is None or end_time_stamp is None:
        today_start, today_end = app.utils.time.get_pst_today_start_and_end()
        return math.floor(today_start.timestamp() * 1000), math.floor(today_end.timestamp() * 1000)
    return int(start_time_stamp), int(end_time_stamp)


@router.get('/daily', response_model=StationDailyResponse)
async def get_daily_view(response: Response,
                         _=Depends(authentication_required),
                         station_codes: Optional[List[int]] = Query(None),
                         start_time_stamp: Optional[int] = None,
                         end_time_stamp: Optional[int] = None):
    """ Returns daily metrics for each station code. """
    try:
        logger.info('/hfi-calc/daily')
        response.headers["Cache-Control"] = no_cache
        valid_start_time, valid_end_time = validate_time_range(start_time_stamp, end_time_stamp)

        async with ClientSession() as session:
            header = await get_auth_header(session)
            wfwx_stations = await app.wildfire_one.wfwx_api.get_wfwx_stations_from_station_codes(
                session, header, station_codes)
            dailies = await get_dailies_lookup_fuel_types(
                session, header, wfwx_stations, valid_start_time, valid_end_time)
            return StationDailyResponse(dailies=dailies)
    except Exception as exc:
        logger.critical(exc, exc_info=True)
        raise


@router.get('/fire-centres', response_model=HFIWeatherStationsResponse)
async def get_fire_centres(response: Response):  # pylint: disable=too-many-locals
    """ Returns list of fire centres and planning area for each fire centre,
    and weather stations within each planning area. Also returns the assigned fuel type
    for each weather station. """
    try:
        logger.info('/hfi-calc/fire-centres')
        response.headers["Cache-Control"] = no_cache

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
                        'order_of_appearance_in_list': planning_area_record.order_of_appearance_in_list,
                        'station_codes': [station_record.station_code],
                        'station_objects': []
                    }
                else:
                    planning_areas_dict[planning_area_record.name]['station_codes'].append(
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
                                                 station_props=station_properties)

                station_info_dict[wfwx_station.code]['station'] = weather_station

                planning_areas_dict[station_info_dict[wfwx_station.code]
                                    ['planning_area'].name]['station_objects'].append(weather_station)

        # create PlanningArea objects containing all corresponding WeatherStation objects
        for key, val in planning_areas_dict.items():
            planning_area = PlanningArea(
                name=key,
                order_of_appearance_in_list=val['order_of_appearance_in_list'],
                stations=val['station_objects'])
            val['planning_area_object'] = planning_area

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
