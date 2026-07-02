"""Standalone entrypoint for the SFMS Daily FWI API service.

This app exists so the SFMS Daily FWI endpoints can be deployed as a separate
internal service (reachable only through the APS Kong gateway) while the main
WPS API keeps its existing public /api surface.
"""

import logging

import sentry_sdk
from fastapi import FastAPI, Request, Response
from starlette.applications import Starlette
from wps_shared import config
from wps_shared.chatops_notification import send_chatops_notification
from wps_shared.wps_logging import configure_logging

from app.routers import sfms_fwi

configure_logging()

logger = logging.getLogger(__name__)

API_INFO = """
    Description: API for SFMS daily FWI rasters

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
    has been specifically advised of the possibility of such damages."""

if config.get("ENVIRONMENT") == "production":
    sentry_sdk.init(
        dsn=config.get("SENTRY_DSN"),
        environment=config.get("ENVIRONMENT"),
        traces_sample_rate=0.5,
        profiles_sample_rate=0.5,
    )

api = FastAPI(title="SFMS Daily FWI API", description=API_INFO, version="0.0.0")
app = Starlette()
app.mount("/api", app=api)


async def catch_exception_middleware(request: Request, call_next):
    """Basic middleware to catch all unhandled exceptions and log them to the terminal."""
    try:
        return await call_next(request)
    except Exception as exc:
        logger.error("%s %s %s", request.method, request.url.path, exc, exc_info=True)
        rc_message = f"Exception occurred {request.method} {request.url.path}"
        send_chatops_notification(rc_message, exc)
        raise


app.middleware("http")(catch_exception_middleware)
api.middleware("http")(catch_exception_middleware)

api.include_router(sfms_fwi.router, tags=["SFMS Daily FWI"])


@api.get("/ready")
async def get_ready():
    """A simple endpoint for OpenShift readiness."""
    return Response()


@api.get("/health")
async def get_health():
    """A simple endpoint for OpenShift healthchecks.

    This service only reads from the object store — it has no database
    dependency, so being up is being healthy."""
    return {"healthy": True, "message": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
