""" Routers for HFI Calculator """
import logging
import json
from typing import List, Optional, Dict, Tuple
from datetime import date
from jinja2 import Environment, FunctionLoader
from fastapi import APIRouter, Response, Depends
from pydantic.error_wrappers import ValidationError
from sqlalchemy.orm import Session
from app.utils.time import get_pst_now
from app.hfi import calculate_latest_hfi_results, hydrate_fire_centres
from app.hfi.pdf_generator import generate_pdf
from app.hfi.pdf_template import get_template
from app.hfi.hfi_calc import (initialize_planning_area_fire_starts,
                              validate_date_range,
                              load_fire_start_ranges)
from app.schemas.hfi_calc import (HFIResultRequest,
                                  HFIResultResponse,
                                  FireStartRange,
                                  StationInfo,
                                  DateRange)
from app.auth import (auth_with_select_station_role_required,
                      auth_with_set_fire_starts_role_required,
                      authentication_required,
                      audit)
from app.schemas.hfi_calc import HFIWeatherStationsResponse
from app.db.crud.hfi_calc import (get_most_recent_updated_hfi_request,
                                  get_most_recent_updated_hfi_request_for_current_date,
                                  store_hfi_request,
                                  get_fire_centre_stations)
from app.db.database import get_read_session_scope, get_write_session_scope


logger = logging.getLogger(__name__)


no_cache = "max-age=0"  # don't let the browser cache this

router = APIRouter(
    prefix="/hfi-calc",
    dependencies=[Depends(authentication_required), Depends(audit)]
)


def get_prepared_request(
        session: Session,
        fire_centre_id: int,
        date_range: Optional[DateRange]) -> Tuple[HFIResultRequest, bool, List[FireStartRange]]:
    """ Attempt to load the most recent request from the database, failing that creates a new request all
    set up with default values.

    TODO: give this function a better name.
    """
    fire_centre_fire_start_ranges = list(load_fire_start_ranges(session, fire_centre_id))
    if date_range:
        stored_request = get_most_recent_updated_hfi_request(session,
                                                             fire_centre_id,
                                                             date_range)
        # NOTE: We could be real nice here, and look for a prep period that intercepts, and grab data there.
    else:
        # No date range specified!
        stored_request = get_most_recent_updated_hfi_request_for_current_date(session, fire_centre_id)
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
        selected_station_code_ids = set()
        planning_area_station_info: Dict[int, List[StationInfo]] = {}
        planning_area_fire_starts: Dict[int, FireStartRange] = {}
        date_range = validate_date_range(date_range)

        num_prep_days = date_range.days_in_range()

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
            date_range=date_range,
            selected_fire_center_id=fire_centre_id,
            selected_station_code_ids=list(selected_station_code_ids),
            planning_area_fire_starts=planning_area_fire_starts,
            planning_area_station_info=planning_area_station_info)

    return result_request, request_loaded, fire_centre_fire_start_ranges


async def calculate_and_create_response(
        session: Session,
        result_request: HFIResultRequest,
        fire_centre_fire_start_ranges: List[FireStartRange]) -> HFIResultResponse:
    """ Calculate the HFI results and create a response object. """

    (results,
     valid_date_range) = await calculate_latest_hfi_results(
        session,
        result_request,
        fire_centre_fire_start_ranges)

    # Construct the response object.
    return HFIResultResponse(
        date_range=valid_date_range,
        planning_area_station_info=result_request.planning_area_station_info,
        selected_fire_center_id=result_request.selected_fire_center_id,
        planning_area_hfi_results=results,
        fire_start_ranges=fire_centre_fire_start_ranges)


def save_request_in_database(request: HFIResultRequest, username: str) -> bool:
    """ Save the request to the database (if there's a valid prep period).

    Returns:
        True if the request was saved, False otherwise.
    """
    if request.date_range is not None and \
            request.date_range.start_date is not None and \
            request.date_range.end_date is not None:
        with get_write_session_scope() as session:
            store_hfi_request(session, request, username)
            return True
    return False


@router.post("/fire_centre/{fire_centre_id}/{start_date}/{end_date}/planning_area/{planning_area_id}"
             "/station/{station_code}/selected/{enable}")
async def set_planning_area_station(
    fire_centre_id: int, start_date: date, end_date: date,
    planning_area_id: int, station_code: int,
    enable: bool,
    response: Response,
    token=Depends(auth_with_select_station_role_required)
):
    """ Enable / disable a station withing a planning area """
    logger.info('/fire_centre/%s/%s/%s/planning_area/%s/station/%s/selected/%s',
                fire_centre_id, start_date, end_date, planning_area_id, station_code, enable)
    response.headers["Cache-Control"] = no_cache

    with get_read_session_scope() as session:
        # We get an existing request object (it will load from the DB or create it
        # from scratch if it doesn't exist).
        request, _, fire_centre_fire_start_ranges = get_prepared_request(session,
                                                                         fire_centre_id,
                                                                         DateRange(
                                                                             start_date=start_date,
                                                                             end_date=end_date))

        # Set the station selected or not.
        station_info_list = request.planning_area_station_info[planning_area_id]
        station_info = next(info for info in station_info_list if info.station_code == station_code)
        station_info.selected = enable

        # Get the response.
        request_response = await calculate_and_create_response(
            session, request, fire_centre_fire_start_ranges)

    # We save the request in the database. (We do this right at the end, so that we don't
    # save a broken request by accident.)
    save_request_in_database(request, token.get('preferred_username', None))
    return request_response


@router.post("/fire_centre/{fire_centre_id}/{start_date}/{end_date}/planning_area/{planning_area_id}"
             "/station/{station_code}/fuel_type/{fuel_type_id}")
async def set_planning_area_station_fuel_type(
    fire_centre_id: int,
    start_date: date,
    end_date: date,
    planning_area_id: int,
    station_code: int,
    fuel_type_id: int,
    response: Response,
    token=Depends(authentication_required)  # pylint: disable=unused-argument
):
    """ Set the fuel type for a station in a planning area. """
    # TODO: stub - implement!
    logger.info("/fire_centre/%s/%s/%s/planning_area/%s/station/%s/fuel_type/%s",
                fire_centre_id, start_date, end_date,
                planning_area_id, station_code, fuel_type_id)
    response.headers["Cache-Control"] = no_cache
    raise NotImplementedError('This function is not implemented yet.')


@router.post("/fire_centre/{fire_centre_id}/{start_date}/{end_date}/planning_area/{planning_area_id}"
             "/fire_starts/{prep_day_date}/fire_start_range/{fire_start_range_id}",
             response_model=HFIResultResponse)
async def set_fire_start_range(fire_centre_id: int,
                               start_date: date,
                               end_date: date,
                               planning_area_id: int,
                               prep_day_date: date,
                               fire_start_range_id: int,
                               response: Response,
                               token=Depends(auth_with_set_fire_starts_role_required)):
    """ Set the fire start range, by id."""
    logger.info("/fire_centre/%s/%s/%s/planning_area/%s"
                "/fire_starts/%s/fire_start_range/%s",
                fire_centre_id, start_date, end_date,
                planning_area_id,
                prep_day_date, fire_start_range_id)
    response.headers["Cache-Control"] = no_cache

    with get_read_session_scope() as session:
        # We get an existing request object (it will load from the DB or create it
        # from scratch if it doesn't exist).
        request, _, fire_centre_fire_start_ranges = get_prepared_request(session,
                                                                         fire_centre_id,
                                                                         DateRange(start_date=start_date,
                                                                                   end_date=end_date))

        # We set the fire start range in the planning area for the provided prep day.
        if prep_day_date <= request.date_range.end_date:
            delta = prep_day_date - request.date_range.start_date
            fire_start_range = next(item for
                                    item in fire_centre_fire_start_ranges if item.id == fire_start_range_id)
            request.planning_area_fire_starts[planning_area_id][delta.days] = FireStartRange(
                id=fire_start_range.id, label=fire_start_range.label)
        else:
            logger.info('prep date falls outside of the prep period')

        # Get the response.
        request_response = await calculate_and_create_response(
            session, request, fire_centre_fire_start_ranges)

    # We save the request in the database.
    save_request_in_database(request, token.get('preferred_username', None))
    return request_response


@router.get("/fire_centre/{fire_centre_id}", response_model=HFIResultResponse)
async def get_hfi_result(fire_centre_id: int,
                         response: Response,
                         token=Depends(authentication_required)):
    """ Given a fire centre id, load the most recent HFIResultRequest.
    If there isn't a stored request, one will be created.
    """
    logger.info('/hfi-calc/load/%s', fire_centre_id)
    response.headers["Cache-Control"] = no_cache
    return await get_hfi_result_with_date(fire_centre_id, None, None, response, token)


@router.get("/fire_centre/{fire_centre_id}/{start_date}/{end_date}", response_model=HFIResultResponse)
async def get_hfi_result_with_date(fire_centre_id: int,
                                   start_date: Optional[date],
                                   end_date: Optional[date],
                                   response: Response,
                                   _=Depends(authentication_required)):
    """ Given a fire centre id (and optionally a start date), load the most recent HFIResultRequest.
    If there isn't a stored request, one will be created.
    """
    try:
        logger.info('/hfi-calc/load/%s/%s/%s', fire_centre_id, start_date, end_date)
        response.headers["Cache-Control"] = no_cache

        with get_read_session_scope() as session:
            if start_date and end_date:
                date_range = DateRange(start_date=start_date, end_date=end_date)
            else:
                date_range = None
            request, _, fire_centre_fire_start_ranges = get_prepared_request(session,
                                                                             fire_centre_id,
                                                                             date_range)

            # Get the response.
            request_response = await calculate_and_create_response(
                session, request, fire_centre_fire_start_ranges)

        return request_response

    except Exception as exc:
        logger.critical(exc, exc_info=True)
        raise


@router.get('/fire-centres', response_model=HFIWeatherStationsResponse)
async def get_fire_centres(response: Response):
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


@router.get('/fire_centre/{fire_centre_id}/{start_date}/{end_date}/pdf')
async def get_pdf(
    fire_centre_id: int,
    start_date: date,
    end_date: date,
    _: Response,
    token=Depends(authentication_required)
):
    """ Returns a PDF of the HFI results for the supplied fire centre and start date. """
    logger.info('/hfi-calc/fire_centre/%s/%s/%s/pdf', fire_centre_id, start_date, end_date)

    with get_read_session_scope() as session:
        (request,
         _,
         fire_centre_fire_start_ranges) = get_prepared_request(session,
                                                               fire_centre_id,
                                                               DateRange(start_date=start_date,
                                                                         end_date=end_date))

        # Get the response.
        request_response = await calculate_and_create_response(
            session, request, fire_centre_fire_start_ranges)

    fire_centres_list = await hydrate_fire_centres()

    # Loads template as string from a function
    # See: https://jinja.palletsprojects.com/en/3.0.x/api/?highlight=functionloader#jinja2.FunctionLoader
    jinja_env = Environment(loader=FunctionLoader(get_template), autoescape=True)

    username = token.get('preferred_username', None)

    pdf_bytes, pdf_filename = generate_pdf(request_response,
                                           fire_centres_list,
                                           username,
                                           get_pst_now(),
                                           jinja_env)

    return Response(pdf_bytes, headers={'Content-Disposition': f'attachment; filename={pdf_filename}',
                                        'Access-Control-Expose-Headers': 'Content-Disposition',
                                        'Cache-Control': no_cache})
