""" This module contains the entrypoint for the Predictive Services Unit Fire Weather Index calculator API.

See README.md for details on how to run.
"""
import logging
from urllib.request import Request
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk
from starlette.applications import Starlette
from app import configure_logging
from app import config
from app.rocketchat_notifications import send_rocketchat_notification
from app.routers import (sfms)


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

if config.get('ENVIRONMENT') == 'production':        
    sentry_sdk.init(
        dsn=config.get("SENTRY_DSN"),
        environment=config.get('ENVIRONMENT'),
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=0.5,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=0.5,
    )

# This is the api app.
api = FastAPI(
    title="Predictive Services SFMS API",
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

api.include_router(sfms.router, tags=["SFMS", "Auto Spatial Advisory"])


@api.get('/ready')
async def get_ready():
    """ A simple endpoint for OpenShift readiness """
    return Response()


@api.get('/health')
async def get_health():
    """ A simple endpoint for Openshift Healthchecks. """
    return Response()


if __name__ == "__main__":
    # This section of code is for the convenience of developers only. Having this section of code, allows
    # for developers to easily debug the application by running main.py and attaching to it with a debugger.
    # uvicorn is imported in this scope only, as it's not required when the application is run in production.
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
