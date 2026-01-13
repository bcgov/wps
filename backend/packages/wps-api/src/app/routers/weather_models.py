""" Routers for weather_models.
"""
import logging
from typing import List
from aiohttp import ClientSession, TCPConnector
from fastapi import APIRouter, Depends
from datetime import date, datetime, time

from wps_wf1.wfwx_api import WfwxApi
from wps_shared.auth import authentication_required, audit
from wps_shared.utils.time import vancouver_tz
from wps_shared.weather_models import ModelEnum
from wps_shared.schemas.weather_models import WeatherStationModelPredictionValues, WeatherModelPredictionSummaryResponse, WeatherStationsModelRunsPredictionsResponse
from wps_shared.schemas.shared import StationsRequest, WeatherDataRequest
from wps_shared.weather_models.fetch.summaries import fetch_model_prediction_summaries
from wps_shared.weather_models.fetch.predictions import fetch_latest_daily_model_run_predictions_by_station_code_and_date_range, fetch_model_run_predictions_by_station_code

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/weather_models",
    dependencies=[Depends(audit), Depends(authentication_required)],
)


@router.post('/{model}/predictions/summaries/',
             response_model=WeatherModelPredictionSummaryResponse)
async def get_model_prediction_summaries(
        model: ModelEnum, request: WeatherDataRequest):
    """ Returns a summary of predictions for a given model. """
    logger.info('/weather_models/%s/predictions/summaries/', model.name)
    conn = TCPConnector(limit=10)
    async with ClientSession(connector=conn) as client_session:
        wfwx_api = WfwxApi(client_session)
        stations = wfwx_api.get_stations_by_codes(request.stations)
    summaries = fetch_model_prediction_summaries(
        model, request.stations, request.time_of_interest, stations
    )

    return WeatherModelPredictionSummaryResponse(summaries=summaries)


@router.post('/{model}/predictions/most_recent/',
             response_model=WeatherStationsModelRunsPredictionsResponse)
async def get_most_recent_model_values(
        model: ModelEnum, request: WeatherDataRequest):
    """ Returns the weather values for the last model prediction that was issued
    for the station before actual weather readings became available.
    """
    logger.info('/weather_models/%s/predictions/most_recent/', model.name)
    async with ClientSession() as client_session:
        wfwx_api = WfwxApi(client_session)
        all_stations = wfwx_api.get_stations_by_codes(request.stations)
    station_predictions = fetch_model_run_predictions_by_station_code(
        model, request.stations, request.time_of_interest, all_stations
    )

    return WeatherStationsModelRunsPredictionsResponse(
        stations=station_predictions)


@router.post('/{model}/predictions/most_recent/{start_date}/{end_date}',
             response_model=List[WeatherStationModelPredictionValues])
async def get_model_values_for_date_range(
        model: ModelEnum, start_date: date, end_date: date, request: StationsRequest):
    """ Returns the weather values for the last model prediction for the 
    requested stations within the requested date range.
    """
    logger.info('/weather_models/%s/predictions/most_recent/%s/%s', model.name, start_date, end_date)

    start_time = datetime.combine(start_date, time.min, tzinfo=vancouver_tz)
    end_time = datetime.combine(end_date, time.max, tzinfo=vancouver_tz)
    conn = TCPConnector(limit=10)
    async with ClientSession(connector=conn) as client_session:
        wfwx_api = WfwxApi(client_session)
        all_stations = wfwx_api.get_stations_by_codes(request.stations)

    station_predictions = fetch_latest_daily_model_run_predictions_by_station_code_and_date_range(
        model, request.stations, start_time, end_time, all_stations
    )

    return station_predictions
