""" This module contains the entrypoint for the Predictive Services Unit Fire Weather Index calculator API.

See README.md for details on how to run.
"""
import datetime
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app import schemas, configure_logging
from app.models.fetch.predictions import fetch_model_predictions
from app.models.fetch.summaries import fetch_model_prediction_summaries
from app.models import ModelEnum
from app.percentile import get_precalculated_percentiles
from app.forecasts.noon_forecasts import fetch_noon_forecasts
from app.forecasts.noon_forecasts_summaries import fetch_noon_forecasts_summaries
from app.auth import authenticate
from app import config
from app import health
from app import hourlies
from app import stations
import app.time_utils as time_utils


configure_logging()

LOGGER = logging.getLogger(__name__)

API_INFO = '''
    Description: API for the PSU FWI Calculator

    Warranty Disclaimer:

    This 90th Percentile Forest Fire Weather Index(FWI) system software
    and related documentation is provided as a public service by the
    Government of British Columbia, Box 9411, Victoria, British
    Columbia, Canada V8W 9V1.

    This 90th Percentile Forest Fire Weather Index(FWI) system software
    and related documentation are provided \"as is\" without
    warranty of any kind, whether express or implied. Users of this
    software and documentation do so at their own risk. All implied
    warranties, including, without limitation, implied warranties of
    merchantability, fitness for a particular purpose, and
    non - infringement, are hereby expressly disclaimed. Links and
    references to any other websites or software are provided for
    information only and listing shall not be taken as endorsement of
    any kind.

    The Government of British Columbia is not responsible for the
    content or reliability of any linked software and websites and does
    not endorse the content, products, services or views expressed
    within them. It is the responsibility of all persons who use 90th
    Percentile Forest Fire Weather Index(FWI) system software and
    related documentation to independently confirm the accuracy of the
    data, information, or results obtained through their use.

    Limitation of Liabilities Under no circumstances will the Government
    of British Columbia be liable to any person or business entity for
    any direct, indirect, special, incidental, consequential, or other
    damages based on any use of this software and documentation or any
    other software to which this site is linked, including, without
    limitation, any lost profits, business interruption, or loss of
    programs or information, even if the Government of British Columbia
    has been specifically advised of the possibility of such damages.'''


app = FastAPI(
    title="Predictive Services Fire Weather Index Calculator",
    description=API_INFO,
    version="0.0.0"
)

ORIGINS = config.get('ORIGINS')

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get('/health')
async def get_health():
    """ A simple endpoint for Openshift Healthchecks """
    try:
        health_check = health.patroni_cluster_health_check()
        LOGGER.info('/health - healthy: %s. %s',
                    health_check.get('healthy'), health_check.get('message'))
        return health_check
    except Exception as exception:
        LOGGER.error(exception, exc_info=True)
        raise


@app.post('/models/{model}/predictions/', response_model=schemas.WeatherModelPredictionResponse)
async def get_model_predictions(
        model: ModelEnum, request: schemas.StationCodeList, _: bool = Depends(authenticate)):
    """ Returns 10 day noon prediction based on the global deterministic prediction system (GDPS)
    for the specified set of weather stations. """
    try:
        LOGGER.info('/models/%s/predictions/', model.name)
        model_predictions = await fetch_model_predictions(model, request.stations)
        return schemas.WeatherModelPredictionResponse(predictions=model_predictions)
    except Exception as exception:
        LOGGER.critical(exception, exc_info=True)
        raise


@app.post('/models/{model}/predictions/summaries/',
          response_model=schemas.WeatherModelPredictionSummaryResponse)
async def get_model_prediction_summaries(
        model: ModelEnum, request: schemas.StationCodeList, _: bool = Depends(authenticate)):
    """ Returns a summary of predictions for a given model. """
    try:
        LOGGER.info('/models/%s/predictions/summaries/', model.name)
        summaries = await fetch_model_prediction_summaries(model, request.stations)
        return schemas.WeatherModelPredictionSummaryResponse(summaries=summaries)
    except Exception as exception:
        LOGGER.critical(exception, exc_info=True)
        raise


@app.post('/noon_forecasts/', response_model=schemas.NoonForecastResponse)
def get_noon_forecasts(request: schemas.StationCodeList, _: bool = Depends(authenticate)):
    """ Returns noon forecasts pulled from BC FireWeather Phase 1 website for the specified
    set of weather stations. """
    try:
        LOGGER.info('/noon_forecasts/')
        now = time_utils.get_utc_now()
        back_5_days = now - datetime.timedelta(days=5)
        forward_5_days = now + datetime.timedelta(days=5)
        return fetch_noon_forecasts(request.stations, back_5_days, forward_5_days)
    except Exception as exception:
        LOGGER.critical(exception, exc_info=True)
        raise


@app.post('/noon_forecasts/summaries/', response_model=schemas.NoonForecastSummariesResponse)
async def get_noon_forecasts_summaries(request: schemas.StationCodeList, _: bool = Depends(authenticate)):
    """ Returns summaries of noon forecasts for given weather stations """
    try:
        LOGGER.info('/noon_forecasts/summaries/')
        now = time_utils.get_utc_now()
        back_5_days = now - datetime.timedelta(days=5)
        return await fetch_noon_forecasts_summaries(request.stations, back_5_days, now)

    except Exception as exception:
        LOGGER.critical(exception, exc_info=True)
        raise


@app.post('/hourlies/', response_model=schemas.WeatherStationHourlyReadingsResponse)
async def get_hourlies(request: schemas.StationCodeList, _: bool = Depends(authenticate)):
    """ Returns hourlies for the last 5 days, for the specified weather stations """
    try:
        LOGGER.info('/hourlies/')
        readings = await hourlies.get_hourly_readings(request.stations)
        return schemas.WeatherStationHourlyReadingsResponse(hourlies=readings)
    except Exception as exception:
        LOGGER.critical(exception, exc_info=True)
        raise


@app.get('/stations/', response_model=schemas.WeatherStationsResponse)
async def get_stations():
    """ Return a list of fire weather stations.
    """
    try:
        LOGGER.info('/stations/')
        weather_stations = await stations.get_stations()
        return schemas.WeatherStationsResponse(weather_stations=weather_stations)
    except Exception as exception:
        LOGGER.critical(exception, exc_info=True)
        raise


@app.post('/percentiles/', response_model=schemas.CalculatedResponse)
async def get_percentiles(request: schemas.PercentileRequest):
    """ Return 90% FFMC, 90% ISI, 90% BUI etc. for a given set of fire stations for a given period of time.
    """
    try:
        LOGGER.info('/percentiles/')
        percentiles = get_precalculated_percentiles(request)
        return percentiles
    except Exception as exception:
        LOGGER.critical(exception, exc_info=True)
        raise
