""" This module contains the entrypoint for the Predictive Services Unit Fire Weather Index calculator API.

See README.md for details on how to run.
"""
import logging
from datetime import datetime
from fastapi import FastAPI, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.applications import Starlette
from app import schemas, configure_logging
from app.percentile import get_precalculated_percentiles
from app.auth import authenticate
from app import config
from app import health
from app import hourlies
from app import stations
from app.frontend import frontend
from app.routers import forecasts, weather_models


configure_logging()

logger = logging.getLogger(__name__)

API_INFO = '''
    Description: API for the PSU Services

    Warranty Disclaimer:

    This PSU API and related documentation is provided as a public service by the
    Government of British Columbia, Box 9411, Victoria, British
    Columbia, Canada V8W 9V1.

    This PSU API and related documentation are provided \"as is\" without
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
    within them. It is the responsibility of all persons who use the PSU API
    and documentation to independently confirm the accuracy of the
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
    title="Predictive Services API",
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

api.include_router(forecasts.router)
api.include_router(weather_models.router)


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


@api.post('/observations/', response_model=schemas.observations.WeatherStationHourlyReadingsResponse)
async def get_hourlies(request: schemas.shared.WeatherDataRequest, _: bool = Depends(authenticate)):
    """ Returns hourly observations for the last 5 days, for the specified weather stations """
    try:
        logger.info('/observations/')

        time_of_interest = datetime.fromisoformat(request.time_of_interest)
        readings = await hourlies.get_hourly_readings(request.stations, time_of_interest)

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
