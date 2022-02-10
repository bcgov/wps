""" Routers for HFI Calculator """
import logging
import math
from datetime import date, timedelta
from typing import List, Optional
from aiohttp.client import ClientSession
from fastapi import APIRouter, Response, Depends, Query
from sqlalchemy import over
from sqlalchemy.orm import Session
from app.hfi.hfi import calculate_hfi_results
import app.utils.time
from app.schemas.hfi_calc import (HFIResultRequest,
                                  HFIResultResponse, StationDailyResponse, fire_start_ranges)
import app
import app.db.database
from app.auth import authentication_required, audit
from app.schemas.hfi_calc import (HFIWeatherStationsResponse, WeatherStationProperties,
                                  FuelType, FireCentre, PlanningArea, WeatherStation)
from app.db.crud.hfi_calc import (get_fire_weather_stations,
                                  get_most_recent_fire_centre_prep_period,
                                  create_fire_centre_prep_period,
                                  get_fire_centre_planning_area_selection_overrides,
                                  get_planning_area_overrides_for_day_in_period)
from app.wildfire_one.wfwx_api import (get_auth_header,
                                       get_dailies_lookup_fuel_types,
                                       get_stations_by_codes)


logger = logging.getLogger(__name__)

ageless_cache = "max-age=0"  # don't let the browser cache this

router = APIRouter(
    prefix="/hfi-calc",
    dependencies=[Depends(authentication_required), Depends(audit)]
)


def is_prep_end_date_valid(start_date: date, end_date: date):
    """ Checks if the prep period is valid. Assumes non null start_date """
    if end_date is None:
        return False
    if end_date - start_date > timedelta(days=5):
        return False


def merge_request_prep_period(session: Session, request: HFIResultRequest):
    """ Merge the prep period component of the request from the database with the request from the UI. """
    # TODO: Change request.start_time_stamp and request.end_time_stamp to date.
    if request.start_time_stamp is None or request.end_time_stamp is None:
        # We can use the timestamp from the database.
        prep_period = get_most_recent_fire_centre_prep_period(session, request.selected_fire_center)
        if request.start_time_stamp is None:
            request.start_time_stamp = prep_period.prep_start_day
        if request.end_time_stamp is None:
            request.end_time_stamp = prep_period.prep_end_day
    # Do some data validation - if the data from the request, or from the database is invalid, we fix
    # it here:
    if request.start_time_stamp is None:
        # If for whatever reason we couldn't get a start date, we use a default
        # TODO: Consider fancy logic setting to monday or thursday?
        request.start_time_stamp = date.today()
    if not is_prep_end_date_valid(request.start_time_stamp, request.end_time_stamp):
        # If for whatever reason we couldn't get an end date, we use a default.
        # If for whatever reason the prep perid exceeds 5 days, bring it back down.
        request.end_time_stamp = request.start_time_stamp + timedelta(days=5)
    return request


def merge_planning_area_selection_override(session: Session, request: HFIResultRequest):
    """ Merge the planning area selection overrides from the database with the request from the UI. """
    planning_area_overrides = get_fire_centre_planning_area_selection_overrides(
        session, request.selected_fire_center)

    # If the request hasn't specified a station list at all, we'll just use whatever is in the database.
    # We don't really "merge" the station list - we either use the database, or we use the request as is.
    if request.selected_station_codes is None:
        request.selected_station_codes = []

        for override, fuel_type, station in planning_area_overrides:
            # TODO: we don't have fuel type yet!
            # If we're using the database as our source, and the station is selected, the add it to the list.
            if override.station_selected:
                if station.station_code not in request.selected_station_codes:
                    request.selected_station_codes.append(station.station_code)
    return request


def find_fire_start_range(fire_starts_min: int, fire_starts_max: int):
    # TODO: this is hellu ugly - need to relook that structure
    return next(fire_start_range for fire_start_range in fire_start_ranges
                if fire_start_range.fire_starts_min == fire_starts_min
                and fire_start_range.fire_starts_max == fire_starts_max)


def merge_planning_area_selection_override_for_day(session: Session, request: HFIResultRequest):
    planning_area_overrides = get_planning_area_overrides_for_day_in_period(
        session, request.selected_fire_center, request.start_time_stamp, request.end_time_stamp)

    period = request.end_time_stamp - request.start_time_stamp

    # If the request hasn't specified fire starts, then we'll just use whatever is in the database.
    if request.planning_area_fire_starts is None:
        for override in planning_area_overrides:
            if override.planning_area_id not in request.planning_area_fire_starts.keys:
                # create a list of fire starts for this planning area
                request.planning_area_fire_starts[override.planning_area_id] = [None] * period.days
            delta = request.start_time_stamp - override.day
            request.planning_area_fire_starts[override.planning_area_id][delta.days] = find_fire_start_range(
                override.fire_starts_min, override.fire_starts_max)

    return request


def merge_request_with_overrides(session: Session, request: HFIResultRequest):
    """ Merge the request from the UI with the overrides from the database, with the UI taking precedence. """
    with app.db.database.get_read_session_scope() as session:
        request = merge_request_prep_period(session, request)
        request = merge_planning_area_selection_override(session, request)
        request = merge_planning_area_selection_override_for_day(session, request)
    return request


def store_request(request: HFIResultRequest):
    """ Store the request in the database. """
    # TODO: we need some kind of flag (corresponding to a save button)
    save = True
    if save:
        if request.start_time_stamp is not None or request.end_time_stamp is not None:
            with app.db.database.get_write_session_scope() as session:
                create_fire_centre_prep_period(session,
                                               request.selected_fire_center,
                                               request.start_time_stamp,
                                               request.end_time_stamp)


@router.post('/', response_model=HFIResultResponse)
async def get_hfi_results(request: HFIResultRequest,
                          response: Response,
                          _=Depends(authentication_required)):
    """ Returns calculated HFI results for the supplied details in the POST body """

    try:
        logger.info('/hfi-calc/')
        request = merge_request_with_overrides(request)
        store_request(request)
        response.headers["Cache-Control"] = ageless_cache
        valid_start_time, valid_end_time = validate_time_range(
            request.start_time_stamp, request.end_time_stamp)

        async with ClientSession() as session:
            header = await get_auth_header(session)
            wfwx_stations = await app.wildfire_one.wfwx_api.get_wfwx_stations_from_station_codes(
                session, header, request.station_codes)
            dailies = await get_dailies_lookup_fuel_types(
                session, header, wfwx_stations, valid_start_time, valid_end_time)
            results = calculate_hfi_results(request.selected_fire_center,
                                            request.planning_area_fire_starts,
                                            dailies, request.num_prep_days,
                                            request.selected_station_codes)
        return HFIResultResponse(
            num_prep_days=request.num_prep_days,
            selected_prep_date=request.selected_prep_date,
            start_time_stamp=valid_start_time,
            end_time_stamp=valid_end_time,
            selected_station_codes=request.selected_station_codes,
            selected_fire_center=request.selected_fire_center,
            planning_area_hfi_results=results,
            planning_area_fire_starts=request.planning_area_fire_starts)
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
        response.headers["Cache-Control"] = ageless_cache
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
        response.headers["Cache-Control"] = ageless_cache

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
