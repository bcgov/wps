""" Routers for HFI Calculator """
import logging
import json
from typing import List, Optional, Dict, Tuple
from datetime import date
from jinja2 import Environment, FunctionLoader
from fastapi import APIRouter, HTTPException, Response, Depends, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from pydantic.error_wrappers import ValidationError
from app.hfi.fire_centre_cache import (clear_cached_hydrated_fire_centres,
                                       get_cached_hydrated_fire_centres,
                                       put_cached_hydrated_fire_centres)
from app.hfi.hfi_admin import get_unique_planning_area_ids, update_stations
from app.hfi.hfi_request import update_result_request
from app.utils.time import get_pst_now, get_utc_now
from app.hfi.hfi_calc import calculate_latest_hfi_results, hydrate_fire_centres
from app.hfi.pdf_generator import generate_pdf
from app.hfi.pdf_template import get_template
from app.hfi.hfi_calc import (initialize_planning_area_fire_starts,
                              validate_date_range,
                              load_fire_start_ranges)
from app.schemas.hfi_calc import (HFIAdminStationUpdateRequest, HFIAllReadyStatesResponse,
                                  HFIResultRequest,
                                  HFIResultResponse,
                                  FireStartRange, HFIReadyState,
                                  StationInfo,
                                  DateRange,
                                  FuelTypesResponse,
                                  HFIWeatherStationsResponse)
from app.auth import (auth_with_select_station_role_required,
                      auth_with_set_fire_starts_role_required,
                      auth_with_station_admin_role_required,
                      auth_with_set_fuel_type_role_required,
                      auth_with_set_ready_state_required,
                      authentication_required,
                      audit)
from app.schemas.shared import (FuelType)
from app.db.crud.hfi_calc import (get_fuel_type_by_id,
                                  get_most_recent_updated_hfi_request,
                                  get_most_recent_updated_hfi_request_for_current_date,
                                  get_planning_weather_stations,
                                  get_latest_hfi_ready_records, get_stations_for_affected_planning_areas,
                                  get_stations_for_removal,
                                  store_hfi_request,
                                  get_fire_centre_stations,
                                  toggle_ready, save_hfi_stations, unready_planning_areas)
from app.db.crud.hfi_calc import get_fuel_types as crud_get_fuel_types
import app.db.models.hfi_calc
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
    # pylint: disable=too-many-locals
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
            latest_stations = get_planning_weather_stations(session, fire_centre_id)
            result_request = update_result_request(
                HFIResultRequest.parse_obj(json.loads(stored_request.request)),
                latest_stations)
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


def fuel_type_model_to_schema(fuel_type_record: app.db.models.hfi_calc.FuelType) -> FuelType:
    """ Parse a database model record into a schema record. """
    return FuelType(id=fuel_type_record.id, description=fuel_type_record.description,
                    abbrev=fuel_type_record.abbrev,
                    fuel_type_code=fuel_type_record.fuel_type_code,
                    percentage_conifer=fuel_type_record.percentage_conifer,
                    percentage_dead_fir=fuel_type_record.percentage_dead_fir)


@router.get("/fuel_types")
async def get_fuel_types(response: Response) -> FuelTypesResponse:
    """ Return list of fuel type records pulled from database. """
    logger.info('/fuel_types/')
    # allow browser to cache fuel_types for 1 week because they won't change often (or possibly ever)
    response.headers["Cache-Control"] = "max-age=604800"

    with get_read_session_scope() as session:
        result = crud_get_fuel_types(session)
    fuel_types = []
    for fuel_type_record in result:
        fuel_types.append(fuel_type_model_to_schema(fuel_type_record))
    return FuelTypesResponse(fuel_types=fuel_types)


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
    save_request_in_database(request, token.get('idir_username', None))
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
    token=Depends(auth_with_set_fuel_type_role_required)
):
    """ Set the fuel type for a station in a planning area. """
    logger.info("/fire_centre/%s/%s/%s/planning_area/%s/station/%s/fuel_type/%s",
                fire_centre_id, start_date, end_date,
                planning_area_id, station_code, fuel_type_id)
    response.headers["Cache-Control"] = no_cache

    with get_read_session_scope() as session:
        # We get an existing request object (it will load from the DB or create it
        # from scratch if it doesn't exist).
        request, _, fire_centre_fire_start_ranges = get_prepared_request(
            session,
            fire_centre_id,
            DateRange(start_date=start_date,
                      end_date=end_date))

        # Validate the fuel type id.
        fuel_type = get_fuel_type_by_id(session, fuel_type_id)
        if fuel_type is None:
            raise HTTPException(status_code=500, detail="Fuel type not found")

        # Set the fuel type for the station.
        station_info_list = request.planning_area_station_info[planning_area_id]
        station_info = next(info for info in station_info_list if info.station_code == station_code)
        station_info.fuel_type_id = fuel_type_id

        request_response = await calculate_and_create_response(
            session, request, fire_centre_fire_start_ranges)

    save_request_in_database(request, token.get('idir_username', None))
    return request_response


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
    save_request_in_database(request, token.get('idir_username', None))
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
    logger.info('/hfi-calc/fire-centres')
    response.headers["Cache-Control"] = no_cache

    # Attempt to retrieve from cache
    cached_response = await get_cached_hydrated_fire_centres()
    if cached_response is not None:
        return cached_response
    fire_centres_list = await hydrate_fire_centres()
    response = HFIWeatherStationsResponse(fire_centres=fire_centres_list)
    await put_cached_hydrated_fire_centres(response)
    return response


@router.get('/fire_centre/{fire_centre_id}/{start_date}/{end_date}/ready')
async def get_all_ready_records(
    fire_centre_id: int,
    start_date: date,
    end_date: date,
    response: Response,
    _=Depends(authentication_required)
):
    logger.info("/fire_centre/%s/start_date/%s/end_date/%s/ready", fire_centre_id, start_date, end_date)
    response.headers["Cache-Control"] = no_cache

    with get_read_session_scope() as session:
        hfi_request = get_most_recent_updated_hfi_request(session,
                                                          fire_centre_id,
                                                          DateRange(
                                                              start_date=start_date,
                                                              end_date=end_date))
        if hfi_request is None:
            return HFIAllReadyStatesResponse(ready_states=[])
        ready_states: List[HFIReadyState] = []
        ready_records: List[app.db.models.hfi_calc.HFIReady] = get_latest_hfi_ready_records(session, hfi_request.id)
        for record in ready_records:
            ready_states.append(HFIReadyState(planning_area_id=record.planning_area_id,
                                              hfi_request_id=record.hfi_request_id,
                                              ready=record.ready,
                                              create_timestamp=record.create_timestamp,
                                              create_user=record.create_user,
                                              update_timestamp=record.update_timestamp,
                                              update_user=record.update_user))
        return HFIAllReadyStatesResponse(ready_states=ready_states)


@router.post("/fire_centre/{fire_centre_id}/planning_area/{planning_area_id}/{start_date}/{end_date}/ready",
             response_model=HFIReadyState)
async def toggle_planning_area_ready(
        fire_centre_id: int,
        planning_area_id: int,
        start_date: date,
        end_date: date, response: Response,
        token=Depends(auth_with_set_ready_state_required)):
    """ Set the fire start range, by id."""
    logger.info("/fire_centre/%s/planning_area/%s/start_date/%s/end_date/%s/ready",
                fire_centre_id, planning_area_id, start_date, end_date)
    response.headers["Cache-Control"] = no_cache

    with get_write_session_scope() as session:
        username = token.get('idir_username', None)
        ready_state = toggle_ready(session, fire_centre_id, planning_area_id, DateRange(
            start_date=start_date,
            end_date=end_date),
            username)
        response = HFIReadyState(planning_area_id=ready_state.planning_area_id,
                                 hfi_request_id=ready_state.hfi_request_id,
                                 ready=ready_state.ready,
                                 create_timestamp=ready_state.create_timestamp,
                                 create_user=ready_state.create_user,
                                 update_timestamp=ready_state.update_timestamp,
                                 update_user=ready_state.update_user)
        return response


@router.post('/admin/stations', status_code=status.HTTP_200_OK)
async def admin_update_stations(request: HFIAdminStationUpdateRequest,
                                token=Depends(auth_with_station_admin_role_required)):
    """ Apply updates for a list of stations. """
    logger.info('/hfi-calc/admin/stations')
    username = token.get('idir_username', None)
    with get_write_session_scope() as db_session:
        timestamp = get_utc_now()
        stations_to_remove = get_stations_for_removal(db_session, request.removed)
        all_planning_area_stations = get_stations_for_affected_planning_areas(db_session, request)
        stations_to_save = update_stations(
            stations_to_remove,
            all_planning_area_stations,
            request.added,
            timestamp,
            username)
        affected_planning_area_ids = get_unique_planning_area_ids(stations_to_save)
        try:
            save_hfi_stations(db_session, stations_to_save)
            unready_planning_areas(db_session, request.fire_centre_id,
                                   username, affected_planning_area_ids)
            clear_cached_hydrated_fire_centres()
        except IntegrityError as exception:
            logger.info(exception, exc_info=exception)
            db_session.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,  # pylint: disable=raise-missing-from
                                detail="Station already exists in planning area")


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

        fuel_types_result = crud_get_fuel_types(session)
        fuel_types: Dict[int, FuelType] = {fuel_type_record.id: fuel_type_model_to_schema(
            fuel_type_record) for fuel_type_record in fuel_types_result}

    fire_centres_list = await hydrate_fire_centres()

    # Loads template as string from a function
    # See: https://jinja.palletsprojects.com/en/3.0.x/api/?highlight=functionloader#jinja2.FunctionLoader
    jinja_env = Environment(loader=FunctionLoader(get_template), autoescape=True)

    username = token.get('idir_username', None)

    pdf_bytes, pdf_filename = generate_pdf(request_response,
                                           fire_centres_list,
                                           username,
                                           get_pst_now(),
                                           jinja_env,
                                           fuel_types)

    return Response(pdf_bytes, headers={'Content-Disposition': f'attachment; filename={pdf_filename}',
                                        'Access-Control-Expose-Headers': 'Content-Disposition',
                                        'Cache-Control': no_cache})
