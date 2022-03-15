""" Routers for HFI Calculator """
import logging
import json
from typing import List, Optional
from fastapi import APIRouter, Response, Depends
from app.hfi.daily_pdf_gen import generate_daily_pdf
from app.hfi import calculate_latest_hfi_results, hydrate_fire_centres
import app.utils.time
from app.schemas.hfi_calc import HFIResultRequest, HFIResultResponse, HFILoadResultRequest
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


def load_request_from_database(request: HFIResultRequest) -> Optional[HFIResultRequest]:
    """ If we need to load the request from the database, we do so.

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


@router.post("/load", response_model=HFIResultResponse)
async def load_hfi_result(request: HFILoadResultRequest,
                          response: Response,
                          token=Depends(authentication_required)):
    """ Given a fire centre id (and optionally a start date), load the most recent HFIResultRequst.
    If there isn't a stored request, one will be created.
    """
    try:
        logger.info('/hfi-calc/load/')
        response.headers["Cache-Control"] = no_cache

        with app.db.database.get_read_session_scope() as session:
            stored_request = get_most_recent_updated_hfi_request(session,
                                                                 request.selected_fire_center_id,
                                                                 request.start_date)
            if stored_request:
                result_request = HFIResultRequest.parse_obj(json.loads(stored_request.request))
            else:
                # No stored request, so we need to create one.
                fire_centre_stations = get_fire_centre_stations(session, request.selected_fire_center_id)
                result_request = HFIResultRequest(
                    start_date=request.start_date,
                    selected_fire_center_id=request.selected_fire_center_id,
                    selected_station_code_ids=[station.station_code for station, _ in fire_centre_stations],
                    planning_area_fire_starts={})
                if request.start_date:
                    # If a start date was specified, we go ahead and save this request.
                    save_request_in_database(result_request, token.get('preferred_username', None))

        results, start_timestamp, end_timestamp = await calculate_latest_hfi_results(result_request)
        response = HFIResultResponse(
            start_date=start_timestamp,
            end_date=end_timestamp,
            selected_station_code_ids=result_request.selected_station_code_ids,
            planning_area_station_info=result_request.planning_area_station_info,
            selected_fire_center_id=result_request.selected_fire_center_id,
            planning_area_hfi_results=results,
            planning_area_fire_starts=result_request.planning_area_fire_starts,
            request_persist_success=False)
        return response

    except Exception as exc:
        logger.critical(exc, exc_info=True)
        raise


@router.post('/', response_model=HFIResultResponse)
async def get_hfi_results(request: HFIResultRequest,
                          response: Response,
                          token=Depends(authentication_required)):
    """ Returns calculated HFI results for the supplied details in the POST body """
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

        results, start_timestamp, end_timestamp = await calculate_latest_hfi_results(request)
        response = HFIResultResponse(
            start_date=start_timestamp,
            end_date=end_timestamp,
            selected_station_code_ids=request.selected_station_code_ids,
            planning_area_station_info=request.planning_area_station_info,
            selected_fire_center_id=request.selected_fire_center_id,
            planning_area_hfi_results=results,
            planning_area_fire_starts=request.planning_area_fire_starts,
            request_persist_success=False)

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
        results, start_timestamp, end_timestamp = await calculate_latest_hfi_results(request)

        response = HFIResultResponse(
            start_date=start_timestamp,
            end_date=end_timestamp,
            selected_station_code_ids=request.selected_station_code_ids,
            planning_area_station_info=request.planning_area_station_info,
            selected_fire_center_id=request.selected_fire_center_id,
            planning_area_hfi_results=results,
            planning_area_fire_starts=request.planning_area_fire_starts,
            request_persist_success=False)

        fire_centres_list = await hydrate_fire_centres()
        pdf_bytes = generate_daily_pdf(response, fire_centres_list)

        return Response(pdf_bytes)
    except Exception as exc:
        logger.critical(exc, exc_info=True)
        raise
