"""Serves the public Station Weather API through the APS Kong gateway."""

import logging
from contextlib import asynccontextmanager
from textwrap import dedent

import sentry_sdk
from fastapi import Depends, FastAPI, Request, Response
from fastapi.security import APIKeyHeader
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from wps_shared import config
from wps_shared.chatops_notification import send_chatops_notification
from wps_shared.wps_logging import configure_logging
from wps_weather_data.by_station import ByStationTable
from wps_weather_data.by_time import ByTimeTable
from wps_weather_data.stations import StationsTable

from app.routers import station_weather

configure_logging()

logger = logging.getLogger(__name__)

API_INFO = dedent("""
    Description: weather at BC Wildfire Service weather stations: hourly and daily
    observations back to 1987, forecasters' noon forecasts, FWI System indices, and
    weather model values at each station.

    Request access to the Station Weather API through the
    [API Services Portal](https://api.gov.bc.ca). Once approved, send your API key in the
    `X-API-Key` header on data requests. In Swagger UI, select Authorize and enter your key.
    Documentation is publicly accessible.

    Example request:

    ```http
    GET /api/weather/v1/observations/daily?station_codes=322,209&start=2026-07-01&end=2026-07-31
    X-API-Key: YOUR_API_KEY
    ```

    `GET /api/weather/v1/stations` lists the stations. Every endpoint returns CSV instead of
    JSON when sent `Accept: text/csv`.

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
    has been specifically advised of the possibility of such damages.""")

if config.get("ENVIRONMENT") == "production":
    sentry_sdk.init(
        dsn=config.get("SENTRY_DSN"),
        environment=config.get("ENVIRONMENT"),
        traces_sample_rate=0.5,
        profiles_sample_rate=0.5,
    )

# The docs are under /weather because the SFMS API already serves /api/docs on the same
# gateway host.
api = FastAPI(
    title="Station Weather API",
    description=API_INFO,
    version="1.0.0",
    license_info={
        "name": "Access Only",
        "url": "https://www2.gov.bc.ca/gov/content/home/copyright",
    },
    openapi_tags=[
        {"name": "Stations", "description": "The weather stations"},
        {"name": "Observations", "description": "What the stations observed, back to 1987"},
        {"name": "Forecasts", "description": "BC Wildfire Service forecasters' noon forecasts"},
        {"name": "Models", "description": "Weather model values at the stations"},
    ],
    docs_url="/weather/docs",
    redoc_url="/weather/redoc",
    openapi_url="/weather/openapi.json",
)


@asynccontextmanager
async def lifespan(_: Starlette):
    """Open each Delta table once per process: opening one costs most of a second.

    The state goes on the api, which is the app its routes see as `request.app`.
    """
    api.state.by_station_table = ByStationTable()
    api.state.by_time_table = ByTimeTable()
    api.state.stations_table = StationsTable()
    yield


app = Starlette(lifespan=lifespan)
app.mount("/api", app=api)


async def catch_exception_middleware(request: Request, call_next):
    """Basic middleware to catch all unhandled exceptions and log them to the terminal."""
    try:
        return await call_next(request)
    except Exception as exc:
        logger.exception("%s %s", request.method, request.url.path)
        rc_message = f"Exception occurred {request.method} {request.url.path}"
        send_chatops_notification(rc_message, exc)
        raise


app.add_middleware(BaseHTTPMiddleware, dispatch=catch_exception_middleware)
api.middleware("http")(catch_exception_middleware)

# the gateway strips credentials before forwarding requests, so missing keys must be accepted
gateway_api_key = APIKeyHeader(
    name="X-API-Key",
    scheme_name="ApiKeyAuth",
    description="API key issued through the API Services Portal at https://api.gov.bc.ca.",
    auto_error=False,
)

api.include_router(
    station_weather.router,
    prefix="/weather/v1",
    dependencies=[Depends(gateway_api_key)],
    responses={
        401: {"description": "Gateway authentication failed: API key is missing or invalid"},
        429: {"description": "Gateway rate limit exceeded: 60 requests per minute per consumer"},
    },
)


@api.get("/ready", include_in_schema=False)
async def get_ready():
    """A simple endpoint for OpenShift readiness."""
    return Response()


@api.get("/health", include_in_schema=False)
async def get_health():
    """A simple endpoint for OpenShift healthchecks. Requests only read object storage."""
    return {"healthy": True, "message": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8080)
