""" This module contains the entrypoint for the Predictive Services Unit Fire Weather Index calculator API.

See README.md for details on how to run.
"""
import os
import json
import logging
import logging.config
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import schemas
from forecasts import fetch_forecasts
from percentile import get_precalculated_percentiles
from auth import authenticate
import wildfire_one
import config

LOGGING_CONFIG = os.path.join(os.path.dirname(__file__), 'logging.json')
if os.path.exists(LOGGING_CONFIG):
    with open(LOGGING_CONFIG) as config_file:
        CONFIG = json.load(config_file)
    logging.config.dictConfig(CONFIG)
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
    return {"message": "Healthy as ever"}


@app.post('/forecasts/', response_model=schemas.WeatherForecastResponse)
async def get_forecasts(request: schemas.StationCodeList, _: bool = Depends(authenticate)):
    # async def get_forecasts(request: schemas.WeatherForecastRequest):
    """ Returns 10 day noon forecasts based on the global deterministic prediction system (GDPS)
    for the specified set of weather stations. """
    try:
        forecasts = await fetch_forecasts(request.stations)
        return schemas.WeatherForecastResponse(forecasts=forecasts)
    except Exception as exception:
        LOGGER.critical(exception, exc_info=True)
        raise


@app.post('/hourlies/', response_model=schemas.WeatherStationHourlyReadingsResponse)
async def get_hourlies(request: schemas.StationCodeList, _: bool = Depends(authenticate)):
    """ Returns hourlies for the last 5 days, for the specified weather stations """
    try:
        readings = await wildfire_one.get_hourly_readings(request.stations)
        return schemas.WeatherStationHourlyReadingsResponse(hourlies=readings)
    except Exception as exception:
        LOGGER.critical(exception, exc_info=True)
        raise


@app.get('/stations/', response_model=schemas.WeatherStationsResponse)
async def get_stations():
    """ Return a list of fire weather stations.
    """
    try:
        stations = await wildfire_one.get_stations()
        return schemas.WeatherStationsResponse(weather_stations=stations)
    except Exception as exception:
        LOGGER.critical(exception, exc_info=True)
        raise


@app.post('/percentiles/', response_model=schemas.CalculatedResponse)
async def get_percentiles(request: schemas.PercentileRequest):
    """ Return 90% FFMC, 90% ISI, 90% BUI etc. for a given set of fire stations for a given period of time.
    """
    try:
        percentiles = get_precalculated_percentiles(request)
        return percentiles
    except Exception as exception:
        LOGGER.critical(exception, exc_info=True)
        raise
