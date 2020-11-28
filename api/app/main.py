""" This module contains the entrypoint for the Predictive Services Unit Fire Weather Index calculator API.

See README.md for details on how to run.
"""
import datetime
import logging
from fastapi import FastAPI, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.applications import Starlette
from app import schemas, configure_logging
from app.weather_models.fetch.predictions import (
    fetch_model_predictions,
    fetch_predictions_by_station_code,
    fetch_model_run_predictions_by_station_code)
from app.weather_models.fetch.summaries import fetch_model_prediction_summaries
from app.weather_models import ModelEnum, ProjectionEnum
from app.percentile import get_precalculated_percentiles
from app.forecasts.noon_forecasts import fetch_noon_forecasts
from app.forecasts.noon_forecasts_summaries import fetch_noon_forecasts_summaries
from app.auth import authenticate
from app import config
from app import health
from app import hourlies
from app import stations
from app.frontend import frontend
import app.time_utils as time_utils


configure_logging()

logger = logging.getLogger(__name__)

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


# This is the api app.
api = FastAPI(
    title="Predictive Services Fire Weather Index Calculator",
    description=API_INFO,
    version="0.0.0"
)

# This is our base starlette app - it doesn't do much except glue together
# the api and the front end.
app = Starlette()


# The order here is important:
# 1. Mount the /api
# Technically we could leave the api on the root (/), but then you'd get index.html
# instead of a 404 if you have a mistake on your api url.
app.mount('/api', app=api)
# 2. Mount everything else on the root, to the frontend app.
app.mount('/', app=frontend)

ORIGINS = config.get('ORIGINS')

api.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@api.get('/health')
async def get_health():
    """ A simple endpoint for Openshift Healthchecks """
    try:
        health_check = health.patroni_cluster_health_check()
        logger.info('/health - healthy: %s. %s',
                    health_check.get('healthy'), health_check.get('message'))
        return health_check
    except Exception as exception:
        logger.error(exception, exc_info=True)
        raise


@api.post('/models/{model}/predictions/',
          response_model=schemas.weather_models.WeatherModelPredictionResponse)
async def get_model_predictions(
        model: ModelEnum, request: schemas.stations.StationCodeList, _: bool = Depends(authenticate)):
    """ Returns 10 day noon prediction based on the global deterministic prediction system (GDPS)
    for the specified set of weather stations. """
    try:
        logger.info('/models/%s/predictions/', model.name)
        if model == ModelEnum.GDPS:
            projection = ProjectionEnum.LATLON_15X_15
        elif model == ModelEnum.HRDPS:
            projection = ProjectionEnum.HIGH_RES_CONTINENTAL
        else:
            projection = None
        model_predictions = await fetch_model_predictions(model, projection, request.stations)
        return schemas.weather_models.WeatherModelPredictionResponse(predictions=model_predictions)
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise


@api.post('/models/{model}/predictions/summaries/',
          response_model=schemas.weather_models.WeatherModelPredictionSummaryResponse)
async def get_model_prediction_summaries(
        model: ModelEnum, request: schemas.stations.StationCodeList, _: bool = Depends(authenticate)):
    """ Returns a summary of predictions for a given model. """
    try:
        logger.info('/models/%s/predictions/summaries/', model.name)
        summaries = await fetch_model_prediction_summaries(model, request.stations)
        return schemas.weather_models.WeatherModelPredictionSummaryResponse(summaries=summaries)
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise


@api.post('/models/{model}/predictions/historic/most_recent/',
          response_model=schemas.weather_models.WeatherModelPredictionResponse)
async def get_most_recent_historic_model_values(
        model: ModelEnum, request: schemas.stations.StationCodeList, _: bool = Depends(authenticate)):
    """ Returns the weather values for the last model prediction that was issued
    for the station before actual weather readings became available.
    NOTE: This api method can be made redundant - calling /models/{model}/predictions/most_recent/
    will return historic as well as most recent.
    """
    try:
        logger.info('/models/%s/predictions/historic/most_recent/', model.name)
        historic_predictions = await fetch_predictions_by_station_code(model, request.stations,
                                                                       time_utils.get_utc_now())
        return schemas.weather_models.WeatherModelPredictionResponse(predictions=historic_predictions)
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise


@api.post('/models/{model}/predictions/most_recent/',
          response_model=schemas.weather_models.WeatherStationsModelRunsPredictionsResponse)
async def get_most_recent_model_values(
        model: ModelEnum, request: schemas.stations.StationCodeList, _: bool = Depends(authenticate)):
    """ Returns the weather values for the last model prediction that was issued
    for the station before actual weather readings became available.
    """
    try:
        logger.info('/models/%s/predictions/most_recent/', model.name)
        end_date = time_utils.get_utc_now() + datetime.timedelta(days=10)
        station_predictions = await fetch_model_run_predictions_by_station_code(
            model, request.stations, end_date)
        return schemas.weather_models.WeatherStationsModelRunsPredictionsResponse(
            stations=station_predictions)
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise


@api.post('/noon_forecasts/', response_model=schemas.forecasts.NoonForecastResponse)
def get_noon_forecasts(request: schemas.stations.StationCodeList, _: bool = Depends(authenticate)):
    """ Returns noon forecasts pulled from BC FireWeather Phase 1 website for the specified
    set of weather stations. """
    try:
        logger.info('/noon_forecasts/')
        now = time_utils.get_utc_now()
        back_5_days = now - datetime.timedelta(days=5)
        forward_5_days = now + datetime.timedelta(days=5)
        return fetch_noon_forecasts(request.stations, back_5_days, forward_5_days)
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise


@api.post('/noon_forecasts/summaries/', response_model=schemas.forecasts.NoonForecastSummariesResponse)
async def get_noon_forecasts_summaries(request: schemas.stations.StationCodeList,
                                       _: bool = Depends(authenticate)):
    """ Returns summaries of noon forecasts for given weather stations """
    try:
        logger.info('/noon_forecasts/summaries/')
        now = time_utils.get_utc_now()
        back_5_days = now - datetime.timedelta(days=5)
        return await fetch_noon_forecasts_summaries(request.stations, back_5_days, now)

    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise


@api.post('/hourlies/', response_model=schemas.observations.WeatherStationHourlyReadingsResponse)
async def get_hourlies(request: schemas.stations.StationCodeList, _: bool = Depends(authenticate)):
    """ Returns hourlies for the last 5 days, for the specified weather stations """
    try:
        logger.info('/hourlies/')
        readings = await hourlies.get_hourly_readings(request.stations)
        return schemas.observations.WeatherStationHourlyReadingsResponse(hourlies=readings)
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise


@api.get('/stations/', response_model=schemas.stations.WeatherStationsResponse)
async def get_stations(response: Response):
    """ Return a list of fire weather stations.
    """
    try:
        logger.info('/stations/')
        weather_stations = await stations.get_stations()
        response.headers["Cache-Control"] = "max-age=43200"  # let browsers to cache the data for 12 hours
        return schemas.stations.WeatherStationsResponse(weather_stations=weather_stations)
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise


@api.post('/percentiles/', response_model=schemas.percentiles.CalculatedResponse)
async def get_percentiles(request: schemas.percentiles.PercentileRequest):
    """ Return 90% FFMC, 90% ISI, 90% BUI etc. for a given set of fire stations for a given period of time.
    """
    try:
        logger.info('/percentiles/')
        percentiles = get_precalculated_percentiles(request)
        return percentiles
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise


if __name__ == "__main__":
    # This section of code is for the convenience of developers only. Having this section of code, allows
    # for developers to easily debug the application by running main.py and attaching to it with a debugger.
    # uvicorn is imported in this scope only, as it's not required when the application is run in production.
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
