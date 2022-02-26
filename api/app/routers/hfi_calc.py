""" Routers for HFI Calculator """
import logging
import math
from datetime import date, timedelta
from typing import List, Optional
from aiohttp.client import ClientSession
from fastapi import APIRouter, Response, Depends, Query
from app.db.database import get_read_session_scope
from app.hfi.hfi import calculate_hfi_results
import app.utils.time
from app.schemas.hfi_calc import HFIResultRequest, HFIResultResponse, StationDailyResponse
import app
from app.auth import authentication_required, audit
from app.schemas.hfi_calc import (HFIWeatherStationsResponse, WeatherStationProperties,
                                  FuelType, FireCentre, PlanningArea, WeatherStation)
from app.db.crud.hfi_calc import (get_fire_weather_stations,
                                  get_most_recent_updated_hfi_request, store_hfi_request)
from app.wildfire_one.wfwx_api import (get_auth_header,
                                       get_dailies_lookup_fuel_types,
                                       get_stations_by_codes)
from jinja2 import Environment, PackageLoader, select_autoescape


logger = logging.getLogger(__name__)

no_cache = "max-age=0"  # don't let the browser cache this

router = APIRouter(
    prefix="/hfi-calc",
    dependencies=[Depends(authentication_required), Depends(audit)]
)


def load_request(request: HFIResultRequest) -> HFIResultRequest:
    """ If we need to load the request from the database, we do so. Otherwise we return the request as is. """
    if request.start_date is None:
        with app.db.database.get_read_session_scope() as session:
            stored_request = get_most_recent_updated_hfi_request(session, request.selected_fire_center_id)
            if stored_request:
                return HFIResultRequest.parse_obj(stored_request.request)
    return request


def save_request(request: HFIResultRequest, username: str):
    """ Save the request to the database (if there's a valid prep period) """
    if request.start_date is not None and request.end_date is not None:
        with app.db.database.get_write_session_scope() as session:
            store_hfi_request(session, request, username)
    return request


def validate_date_range(start_date: date, end_date: date):
    """ Sets the start_date to today if it is None.
    Set the end_date to start_date + 7 days, if it is None."""
    # we don't have a start date, default to now.
    if start_date is None:
        now = app.utils.time.get_pst_now()
        start_date = date(year=now.year, month=now.month, day=now.day)
    # don't have an end date, default to start date + 5 days.
    if end_date is None:
        end_date = start_date + timedelta(days=5)
    # check if the span exceeds 7, if it does clamp it down to 7 days.
    delta = end_date - start_date
    if delta.days > 7:
        end_date = start_date + timedelta(days=5)
    # check if the span is less than 2, if it is, push it up to 2.
    if delta.days < 2:
        end_date = start_date + timedelta(days=2)
    return start_date, end_date


def extract_selected_stations(request: HFIResultRequest) -> List[int]:
    """ Extract a list of the selected station codes - we use this to get the daily data from wfwx. """
    stations_codes = []
    for _, value in request.planning_area_station_info.items():
        for station_info in value:
            if station_info.selected:
                if not station_info.station_code in stations_codes:
                    stations_codes.append(station_info.station_code)
    return stations_codes


@router.post('/', response_model=HFIResultResponse)
async def get_hfi_results(request: HFIResultRequest,
                          response: Response,
                          token=Depends(authentication_required)):
    """ Returns calculated HFI results for the supplied details in the POST body """

    try:
        logger.info('/hfi-calc/')
        response.headers["Cache-Control"] = no_cache

        request = load_request(request)

        # ensure we have valid start and end dates
        valid_start_date, valid_end_date = validate_date_range(request.start_date, request.end_date)
        # wf1 talks in terms of timestamps, so we convert the dates to the correct timestamps.
        start_timestamp = int(app.utils.time.get_hour_20_from_date(valid_start_date).timestamp() * 1000)
        end_timestamp = int(app.utils.time.get_hour_20_from_date(valid_end_date).timestamp() * 1000)

        selected_prep_date = request.selected_prep_date
        if selected_prep_date is None \
                or selected_prep_date < valid_start_date or selected_prep_date > valid_end_date:
            selected_prep_date = valid_start_date

        async with ClientSession() as session:
            header = await get_auth_header(session)
            # TODO: Enable when fuel type config implemented
            # selected_station_codes = extract_selected_stations(request)
            wfwx_stations = await app.wildfire_one.wfwx_api.get_wfwx_stations_from_station_codes(
                session, header, request.selected_station_code_ids)
            dailies = await get_dailies_lookup_fuel_types(
                session, header, wfwx_stations, start_timestamp, end_timestamp)
            prep_delta = valid_end_date - valid_start_date  # num prep days is inclusive
            # NOTE: database session brought to this level in order to make code review of
            # calculate_hfi_results easier. (adding session in there, results in the entire function
            # being indented, which makes code review difficult.) Please move session back into
            # function in isolated pr.
            with get_read_session_scope() as orm_session:
                results = calculate_hfi_results(request.selected_fire_center_id,
                                                request.planning_area_fire_starts,
                                                dailies, prep_delta.days,
                                                request.selected_station_code_ids,
                                                orm_session)
        response = HFIResultResponse(
            selected_prep_date=selected_prep_date,
            start_date=start_timestamp,
            end_date=end_timestamp,
            selected_station_code_ids=request.selected_station_code_ids,
            planning_area_station_info=request.planning_area_station_info,
            selected_fire_center_id=request.selected_fire_center_id,
            planning_area_hfi_results=results,
            planning_area_fire_starts=request.planning_area_fire_starts)

        if request.save is True:
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


# @ router.get('/download-pdf')
# async def download_pdf():

#     try:
#         env = Environment(
#             loader=PackageLoader("yourapp"),
#             autoescape=select_autoescape()
#         )

#         template = env.get_template("template1.html")

#         print(template.render(the="variables", go="here"))
#     except Exception as exc:
#         logger.critical(exc, exc_info=True)
#         raise


@ router.get('/daily', response_model=StationDailyResponse)
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
        # we can safely cache the fire centres, as they don't change them very often.
        # the eco-division logic is very slow, and chomps up 2 seconds!
        response.headers["Cache-Control"] = "max-age=86400"

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
