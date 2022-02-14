""" Routers for HFI Calculator """
import logging
import math
from typing import List, Optional, Dict, Union
from aiohttp.client import ClientSession
from fastapi import APIRouter, Response, Depends, Query
from app.db.models.hfi_calc import PlanningWeatherStation, PlanningArea
from app.hfi.hfi import calculate_hfi_results
import app.utils.time
from app.schemas.hfi_calc import HFIResultRequest, HFIResultResponse, StationDailyResponse
import app
from app.auth import authentication_required, audit
from app.schemas.hfi_calc import (HFIWeatherStationsResponse,
                                  WeatherStationProperties, FireCentre, WeatherStation)
from app.db.crud.hfi_calc import get_hydrated_planning_stations
from app.wildfire_one.wfwx_api import (get_auth_header,
                                       get_dailies_lookup_fuel_types,
                                       get_stations_by_codes)


logger = logging.getLogger(__name__)

no_cache = "max-age=0"  # don't let the browser cache this

router = APIRouter(
    prefix="/hfi-calc",
    dependencies=[Depends(authentication_required), Depends(audit)]
)


@router.post('/', response_model=HFIResultResponse)
async def get_hfi_results(request: HFIResultRequest,
                          response: Response,
                          _=Depends(authentication_required)):
    """ Returns calculated HFI results for the supplied details in the POST body """

    try:
        logger.info('/hfi-calc/')
        response.headers["Cache-Control"] = no_cache
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
            hydrated_planning_stations = get_hydrated_planning_stations(session)

            fire_centres: List[FireCentre] = []

            planning_area_dict: Dict[int, PlanningArea] = {
                station.planning_area_id: station.planning_area for station in hydrated_planning_stations}

            fire_centre_dict: Dict[int, FireCentre] = {
                station.planning_area.fire_centre_id: station.planning_area.fire_centre for station in hydrated_planning_stations}

            station_dict: Dict[int, Union[PlanningWeatherStation, WeatherStation]] = {
                station.station_code: station for station in hydrated_planning_stations}

            # We're still missing some data that we need from wfwx, so give it the list of stations
            wfwx_stations = await get_stations_by_codes(list(station_dict.keys()))

            for wfwx_station in wfwx_stations:
                # Hydrate stations further with WFWX data
                planning_station = station_dict[wfwx_station.code]
                station_properties = WeatherStationProperties(
                    name=wfwx_station.name,
                    fuel_type=app.schemas.shared.FuelType(
                        abbrev=planning_station.fuel_type.abbrev,
                        description=planning_station.fuel_type.description),
                    elevation=wfwx_station.elevation,
                    wfwx_station_uuid=wfwx_station.wfwx_station_uuid)

                weather_station = WeatherStation(code=wfwx_station.code,
                                                 station_props=station_properties)
                # Update station dict to point to both planning station and weather station
                station_dict[wfwx_station.code] = (planning_station, weather_station)

        fire_centres: List[FireCentre] = []
        response_planning_area_dict: Dict[int, app.schemas.hfi_calc.PlanningArea] = {}
        for code, (planning_station, weather_station) in station_dict.items():
            planning_area = response_planning_area_dict.get(planning_station.planning_area_id)
            if planning_area is None:
                response_planning_area = app.schemas.hfi_calc.PlanningArea(
                    name=planning_station.planning_area.name,
                    order_of_appearance_in_list=planning_station.planning_area.order_of_appearance_in_list,
                    stations=[weather_station])
                response_planning_area_dict[planning_station.planning_area_id] = response_planning_area
            else:
                planning_area.stations.append(weather_station)

        # create FireCentre objects containing all corresponding PlanningArea objects
        for key, val in fire_centre_dict.items():
            planning_area_objects_list = []
            for pa_record in val['planning_area_records']:
                pa_object = planning_area_dict.get(pa_record.name)
                planning_area_objects_list.append(pa_object)
            fire_centre = FireCentre(name=key, planning_areas=[])
            fire_centres.append(fire_centre)

        return HFIWeatherStationsResponse(fire_centres=fire_centres)

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
