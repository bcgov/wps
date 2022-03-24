""" Routers for HFI Calculator """
import logging
import json
from typing import List, Optional, Mapping, Tuple
from jinja2 import Environment, FunctionLoader
from datetime import date
from fastapi import APIRouter, Response, Depends
from pydantic.error_wrappers import ValidationError
from sqlalchemy.orm import Session
from app.hfi.pdf_generator import generate_pdf
from app.hfi.pdf_template import get_template
from app.hfi import calculate_latest_hfi_results, hydrate_fire_centres
from app.hfi.hfi_calc import (initialize_planning_area_fire_starts,
                              validate_date_range,
                              load_fire_start_ranges)
import app.utils.time
from app.schemas.hfi_calc import FireStartRange, HFIResultRequest, HFIResultResponse, StationInfo
import app
from app.auth import authentication_required, audit
from app.schemas.hfi_calc import (HFIWeatherStationsResponse, WeatherStation)
from app.db.crud.hfi_calc import (get_most_recent_updated_hfi_request, store_hfi_request,
                                  get_fire_centre_stations)


logger = logging.getLogger(__name__)


no_cache = "max-age=0"  # don't let the browser cache this

router = APIRouter(
    prefix="/hfi-calc",
    dependencies=[Depends(authentication_required), Depends(audit)]
)


def get_prepared_request(
        session: Session,
        fire_centre_id: int,
        start_date: Optional[date],
        fire_centre_fire_start_ranges: List[FireStartRange]) -> Tuple[HFIResultRequest, bool]:
    """ Attempt to load the most recent request from the database, failing that creates a new request all
    set up with default values.

    TODO: request_loaded should become redudant once all requests have been changed.
    """

    stored_request = get_most_recent_updated_hfi_request(session,
                                                         fire_centre_id,
                                                         start_date)
    request_loaded = False
    if stored_request:
        try:
            result_request = HFIResultRequest.parse_obj(json.loads(stored_request.request))
            request_loaded = True
        except ValidationError as validation_error:
            # This can happen when we change the schema! It's rare - but it happens.
            logger.error(validation_error)
    if not request_loaded:
        # No stored request, so we need to create one.
        # TODO: selected_station_code_ids make it impossible to have a station selected in one area,
        # and de-selected in another area. This has to be fixed!
        selected_station_code_ids = set()
        planning_area_station_info: Mapping[int, List[StationInfo]] = {}
        planning_area_fire_starts: Mapping[int, FireStartRange] = {}
        start_date, end_date = validate_date_range(start_date, None)
        num_prep_days = (end_date - start_date).days
        fire_centre_stations = get_fire_centre_stations(session, fire_centre_id)
        lowest_fire_starts = fire_centre_fire_start_ranges[0]
        for station, fuel_type in fire_centre_stations:
            selected_station_code_ids.add(station.station_code)
            if station.planning_area_id not in planning_area_station_info:
                planning_area_station_info[station.planning_area_id] = []
            planning_area_station_info[station.planning_area_id].append(
                StationInfo(
                    station_code=station.station_code,
                    selected=True,
                    fuel_type_id=fuel_type.id
                ))
            initialize_planning_area_fire_starts(
                planning_area_fire_starts,
                station.planning_area_id,
                num_prep_days,
                lowest_fire_starts
            )

        result_request = HFIResultRequest(
            start_date=start_date,
            end_date=end_date,
            selected_fire_center_id=fire_centre_id,
            selected_station_code_ids=list(selected_station_code_ids),
            planning_area_fire_starts=planning_area_fire_starts,
            planning_area_station_info=planning_area_station_info)

    return result_request, request_loaded


def load_request_from_database(request: HFIResultRequest) -> Optional[HFIResultRequest]:
    """
    THIS FUNCTION DEPRECATED! Will be removed along with get_hfi_results when all requests have been changed.
    If we need to load the request from the database, we do so.

    Returns:
        The request object if saved, otherwise None.
    """
    if request.start_date is None:
        with app.db.database.get_read_session_scope() as session:
            stored_request = get_most_recent_updated_hfi_request(session, request.selected_fire_center_id)
            if stored_request:
                return HFIResultRequest.parse_obj(json.loads(stored_request.request))
    return None


def save_request_in_database(request: HFIResultRequest, username: str) -> bool:
    """ Save the request to the database (if there's a valid prep period).

    Returns:
        True if the request was saved, False otherwise.
    """
    if request.start_date is not None and request.end_date is not None:
        with app.db.database.get_write_session_scope() as session:
            store_hfi_request(session, request, username)
            return True
    return False


def extract_selected_stations(request: HFIResultRequest) -> List[int]:
    """ Extract a list of the selected station codes - we use this to get the daily data from wfwx. """
    stations_codes = []
    for _, value in request.planning_area_station_info.items():
        for station_info in value:
            if station_info.selected:
                if not station_info.station_code in stations_codes:
                    stations_codes.append(station_info.station_code)
    return stations_codes


@router.post("/fire_centre/{fire_centre_id}/{start_date}/planning_area/{planning_area_id}"
             "/fire_starts/{prep_day_date}/fire_start_range/{fire_start_range_id}",
             response_model=HFIResultResponse)
async def set_fire_start_range(fire_centre_id: int,
                               start_date: date,
                               planning_area_id: int,
                               prep_day_date: date,
                               fire_start_range_id: int,
                               response: Response,
                               token=Depends(authentication_required)):
    """ Set the fire start range, by id."""
    logger.info("/fire_centre/%s/%s/planning_area/%s"
                "/fire_starts/%s/fire_start_range/%s",
                fire_centre_id, start_date, planning_area_id,
                prep_day_date, fire_start_range_id)

    with app.db.database.get_read_session_scope() as session:
        # Load the fire start ranges - it's referenced by a lot of things.
        fire_centre_fire_start_ranges = list(load_fire_start_ranges(session, fire_centre_id))
        # We get an existing request object (it will load from the DB or create it
        # from scratch if it doesn't exist).
        request, _ = get_prepared_request(session,
                                          fire_centre_id,
                                          start_date,
                                          fire_centre_fire_start_ranges)

        # We set the fire start range in the planning area for the provided prep day.
        if prep_day_date <= request.end_date:
            delta = prep_day_date - request.start_date
            fire_start_range = next(item for
                                    item in fire_centre_fire_start_ranges if item.id == fire_start_range_id)
            request.planning_area_fire_starts[planning_area_id][delta.days] = FireStartRange(
                id=fire_start_range.id, label=fire_start_range.label)
        else:
            logger.info('prep date falls outside of the prep period')

        # We calculate the new result.
        (results,
         start_date,
         end_date) = await calculate_latest_hfi_results(session, request, fire_centre_fire_start_ranges)
        # We prepare the response.
        response = HFIResultResponse(
            start_date=start_date,
            end_date=end_date,
            selected_station_code_ids=request.selected_station_code_ids,
            planning_area_station_info=request.planning_area_station_info,
            selected_fire_center_id=request.selected_fire_center_id,
            planning_area_hfi_results=results,
            request_persist_success=False,
            fire_start_ranges=fire_centre_fire_start_ranges)

        # We save the request in the database.
        saved = save_request_in_database(request, token.get('preferred_username', None))
        # TODO: we'll get rid of the request_persist_success param soon.
        response.request_persist_success = saved

    return response


@router.get("/fire_centre/{fire_centre_id}", response_model=HFIResultResponse)
async def load_hfi_result(fire_centre_id: int,
                          response: Response,
                          token=Depends(authentication_required)):
    """ Given a fire centre id, load the most recent HFIResultRequest.
    If there isn't a stored request, one will be created.
    """
    logger.info('/hfi-calc/load/{fire_centre_id}')
    return await load_hfi_result_with_date(fire_centre_id, None, response, token)


@router.get("/fire_centre/{fire_centre_id}/{start_date}", response_model=HFIResultResponse)
async def load_hfi_result_with_date(fire_centre_id: int,
                                    start_date: Optional[date],
                                    response: Response,
                                    token=Depends(authentication_required)):
    """ Given a fire centre id (and optionally a start date), load the most recent HFIResultRequest.
    If there isn't a stored request, one will be created.
    """
    try:
        logger.info('/hfi-calc/load/{fire_centre_id}/{start_date}')
        response.headers["Cache-Control"] = no_cache

        request_persist_success = False
        with app.db.database.get_read_session_scope() as session:
            fire_centre_fire_start_ranges = list(load_fire_start_ranges(session, fire_centre_id))
            result_request, request_loaded = get_prepared_request(session,
                                                                  fire_centre_id,
                                                                  start_date,
                                                                  fire_centre_fire_start_ranges)
            if not request_loaded:
                # If a start date was specified, we go ahead and save this request.
                save_request_in_database(result_request, token.get('preferred_username', None))
                request_persist_success = True

            (results,
             _,
             __) = await calculate_latest_hfi_results(session,
                                                      result_request,
                                                      fire_centre_fire_start_ranges)
        response = HFIResultResponse(
            start_date=result_request.start_date,
            end_date=result_request.end_date,
            selected_station_code_ids=result_request.selected_station_code_ids,
            planning_area_station_info=result_request.planning_area_station_info,
            selected_fire_center_id=result_request.selected_fire_center_id,
            planning_area_hfi_results=results,
            request_persist_success=request_persist_success or request_loaded,
            fire_start_ranges=fire_centre_fire_start_ranges)
        return response

    except Exception as exc:
        logger.critical(exc, exc_info=True)
        raise


@router.post('/', response_model=HFIResultResponse)
async def get_hfi_results(request: HFIResultRequest,
                          response: Response,
                          token=Depends(authentication_required)):
    """ Returns calculated HFI results for the supplied details in the POST body """
    # THIS FUNCTION IS DEPRECATED.
    # Yes. There are a lot of locals!
    # pylint: disable=too-many-locals

    try:
        logger.info('/hfi-calc/')
        response.headers["Cache-Control"] = no_cache

        stored_request = load_request_from_database(request)
        request_loaded = False
        if stored_request:
            request = stored_request
            request_loaded = True

        with app.db.database.get_read_session_scope() as session:
            fire_start_ranges = list(load_fire_start_ranges(session, request.selected_fire_center_id))
            (results,
             start_date,
             end_date) = await calculate_latest_hfi_results(session, request, fire_start_ranges)
        response = HFIResultResponse(
            start_date=start_date,
            end_date=end_date,
            selected_station_code_ids=request.selected_station_code_ids,
            planning_area_station_info=request.planning_area_station_info,
            selected_fire_center_id=request.selected_fire_center_id,
            planning_area_hfi_results=results,
            request_persist_success=False,
            fire_start_ranges=fire_start_ranges)

        # TODO: move this to own function, as part of refactor app.hfi
        request_persist_success = False
        if request.persist_request is True and request_loaded is False:
            # We save the request if we've been asked to, and if we didn't just load it.
            # It's important to do that load check, otherwise we end up saving the request every time
            # we load it!
            save_request_in_database(request, token.get('preferred_username', None))
            request_persist_success = True
        # Indicate in the response if this request is saved in the database.
        response.request_persist_success = request_persist_success or request_loaded
        return response
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
        fire_centres_list = await hydrate_fire_centres()
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


@router.post('/download-pdf')
async def download_result_pdf(request: HFIResultRequest,
                              _=Depends(authentication_required)):
    """ Assembles and returns PDF byte representation of HFI result. """
    try:
        logger.info('/hfi-calc/download-pdf')
        with app.db.database.get_read_session_scope() as session:
            fire_start_ranges = list(load_fire_start_ranges(session, request.selected_fire_center_id))
            (results,
             start_date,
             end_date) = await calculate_latest_hfi_results(session, request, fire_start_ranges)

        response = HFIResultResponse(
            start_date=start_date,
            end_date=end_date,
            selected_station_code_ids=request.selected_station_code_ids,
            planning_area_station_info=request.planning_area_station_info,
            selected_fire_center_id=request.selected_fire_center_id,
            planning_area_hfi_results=results,
            request_persist_success=False,
            fire_start_ranges=fire_start_ranges)

        fire_centres_list = await hydrate_fire_centres()

        # Loads template as string from a function
        # See: https://jinja.palletsprojects.com/en/3.0.x/api/?highlight=functionloader#jinja2.FunctionLoader
        jinja_env = Environment(loader=FunctionLoader(get_template), autoescape=True)

        pdf_bytes = generate_pdf(response, fire_centres_list, jinja_env)

        return Response(pdf_bytes)
    except Exception as exc:
        logger.critical(exc, exc_info=True)
        raise
