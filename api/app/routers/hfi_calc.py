""" Routers for HFI Calculator """
import logging
import json
import io
from time import perf_counter
from datetime import date, timedelta
from typing import AsyncGenerator, List, Optional
from fastapi import APIRouter, Response, Depends
from starlette.responses import StreamingResponse
from app.hfi.daily_pdf_gen import generate_daily_pdf
from app.hfi.hfi import calculate_latest_hfi_results, hydrate_fire_centres
import app.utils.time
from app.schemas.hfi_calc import HFIResultRequest, HFIResultResponse, StationDaily
import app
from app.auth import authentication_required, audit
from app.schemas.hfi_calc import (HFIWeatherStationsResponse, FireCentre, WeatherStation)
from app.db.crud.hfi_calc import (get_most_recent_updated_hfi_request, store_hfi_request)
from app.wildfire_one.schema_parsers import generate_station_daily


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

        # ensure we have valid start and end dates
        valid_start_date, valid_end_date = validate_date_range(request.start_date, request.end_date)
        # wf1 talks in terms of timestamps, so we convert the dates to the correct timestamps.
        start_timestamp = int(app.utils.time.get_hour_20_from_date(valid_start_date).timestamp() * 1000)
        end_timestamp = int(app.utils.time.get_hour_20_from_date(valid_end_date).timestamp() * 1000)

        results = await calculate_latest_hfi_results(
            request, valid_start_date, valid_end_date, start_timestamp, end_timestamp)
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
                              token=Depends(authentication_required)):
    """ Assembles and returns PDF byte representation of HFI result. """
    with open('api/app/tests/hfi/test_hfi_result.json', 'r') as hfi_result, open('api/app/tests/hfi/test_fire_centres.json', 'r') as fcs:
        result = json.load(hfi_result)
        fc_dict = json.load(fcs)
        fire_centres = []
        for fc_json in fc_dict['fire_centres']:
            fc = FireCentre(**fc_json)
            fire_centres.append(fc)
        pdf_bytes = generate_daily_pdf(HFIResultResponse(**result), fire_centres)

    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers={
        'Content-Disposition': 'attachment;filename=test.pdf'
    })
