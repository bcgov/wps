""" This module contains the entrypoint for the Predictive Services Unit Fire Weather Index calculator API.

See README.md for details on how to run.
"""
import logging
from time import perf_counter
from urllib.request import Request
from fastapi import FastAPI, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.applications import Starlette
from app import schemas, configure_logging
from app.percentile import get_precalculated_percentiles
from app.auth import authentication_required, audit
from app import config
from app import health
from app import hourlies
from app.rocketchat_notifications import send_rocketchat_notification
from app.routers import (fba, forecasts, fwi_calc, weather_models, c_haines, stations, hfi_calc,
                         fba_calc)
from app.fire_behaviour.cffdrs import CFFDRS


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


# Mount the /api
# In production, / routes to the frontend. (api and front end run in seperate containers, with
# seperate routing)
app.mount('/api', app=api)

ORIGINS = config.get('ORIGINS')


async def catch_exception_middleware(request: Request, call_next):
    """ Basic middleware to catch all unhandled exceptions and log them to the terminal """
    try:
        return await call_next(request)
    except Exception as exc:
        logger.error('%s %s %s', request.method, request.url.path, exc, exc_info=True)
        rc_message = f"Exception occurred {request.method} {request.url.path}"
        send_rocketchat_notification(rc_message, exc)
        raise

app.middleware('http')(catch_exception_middleware)

api.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
api.middleware('http')(catch_exception_middleware)

api.include_router(forecasts.router, tags=["Forecasts"])
api.include_router(weather_models.router, tags=["Weather Models"])
api.include_router(c_haines.router, tags=["C Haines"])
api.include_router(stations.router, tags=["Stations"])
api.include_router(hfi_calc.router, tags=["HFI"])
api.include_router(fba_calc.router, tags=["FBA Calc"])
api.include_router(fba.router, tags=["FBA"])
api.include_router(fwi_calc.router, tags=["FWI"])
# api.include_router(cog.router, tags=["Cloud Optimized GeoTIFF"])

# cog_router = APIRouter(prefix="/cog")
# cog = TilerFactory()
# cog_router.include_router(cog.router, tags=["Cloud Optimized GeoTIFF"])
# api.include_router(cog_router)

# add_exception_handlers(app, DEFAULT_STATUS_CODES)


@api.get('/ready')
async def get_ready():
    """ A simple endpoint for OpenShift readiness """
    return Response()


@api.get('/health')
async def get_health():
    """ A simple endpoint for Openshift Healthchecks.
    It's assumed that if patroni is ok, then all is well.  """
    try:
        health_check = health.patroni_cluster_health_check()

        logger.debug('/health - healthy: %s. %s',
                     health_check.get('healthy'), health_check.get('message'))

        # Instantiate the CFFDRS singleton. Binding to R can take quite some time...
        cffdrs_start = perf_counter()
        CFFDRS.instance()  # pylint: disable=no-member
        cffdrs_end = perf_counter()
        delta = cffdrs_end - cffdrs_start
        # Any delta below 100 milliseconds is just noise in the logs.
        if delta > 0.1:
            logger.info('%f seconds added by CFFDRS startup', delta)

        return health_check
    except Exception as exception:
        logger.error(exception, exc_info=True)
        raise


@api.post('/observations/', response_model=schemas.observations.WeatherStationHourlyReadingsResponse)
async def get_hourlies(request: schemas.shared.WeatherDataRequest,
                       _=Depends(authentication_required),
                       __=Depends(audit)):
    """ Returns hourly observations for the 5 days before and 10 days after the time of interest
    for the specified weather stations """
    try:
        logger.info('/observations/')

        readings = await hourlies.get_hourly_readings(request.stations, request.time_of_interest)

        return schemas.observations.WeatherStationHourlyReadingsResponse(hourlies=readings)
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
