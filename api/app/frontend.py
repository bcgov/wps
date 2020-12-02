""" Serve up the Single Page Application
"""
import os
import logging
from starlette.applications import Starlette
from starlette.types import Scope
from starlette.routing import Route, Mount
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
from jinja2.exceptions import TemplateNotFound
from app import config

logger = logging.getLogger(__name__)


def get_static_foldername():
    """ Get the static foldername - it defaults to 'static', but can be changed by setting
    an environment variable.
    """
    dirname = os.path.dirname(os.path.abspath(__file__))
    static_foldername = config.get('STATIC_FOLDER', os.path.join(dirname, '../', 'static'))
    return static_foldername


templates = Jinja2Templates(directory=get_static_foldername())


def add_security_headers(scope, response):
    """ Add security headers to statically served content
    """
    path = scope.get('path')

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Content-Type-Options
    if (path and path[path.rfind('.'):] in ('.css', '.js', '.png', '.xml', '.svg', '.json', '.txt'))\
            or response.media_type in ('text/html',):
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    if (path and path[path.rfind('.'):] in ('.xml', '.svg', '.json', '.txt')):
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
        # https://www.zaproxy.org/docs/alerts/10015/
        response.headers.setdefault('Cache-Control', 'no-cache, no-store, must-revalidate;')
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Pragma
        response.headers.setdefault('Pragma', 'no-cache')
    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options
    if response.media_type in ('text/html', 'text/xml'):
        response.headers.setdefault('X-Frame-Options', 'DENY')


class SPAStaticFiles(StaticFiles):
    """ Single Page App Static Files.
    Serves up .(root, or /) whenever a file isn't found.
    For a single page app using routing, we need to serve up
    index.html and let the spa figure out what to serve up.
    NOTE: Ensure html=True is set
    """
    async def get_response(self, path: str, scope: Scope) -> Response:
        # Call the method on the base class.
        response = await super().get_response(path, scope)
        # If file not found, try to serve up index.html
        if response.status_code == 404:
            logger.debug('serving up root for %s', path)
            request = Request(scope)
            return await get_index(request)
        add_security_headers(scope, response)
        logger.debug('serve static: %s', path)
        return response


async def get_index(request: Request):
    """ Apply jina template to index.html
    """
    try:
        response = templates.TemplateResponse(
            "index.html",
            {
                'request': request,
                'REACT_APP_KEYCLOAK_AUTH_URL': config.get('REACT_APP_KEYCLOAK_AUTH_URL'),
                'REACT_APP_KEYCLOAK_REALM': config.get('REACT_APP_KEYCLOAK_REALM'),
                'REACT_APP_KEYCLOAK_CLIENT': config.get('REACT_APP_KEYCLOAK_CLIENT'),
                'REACT_APP_FIDER_LINK': config.get('REACT_APP_FIDER_LINK'),
                'REACT_APP_MATOMO_URL': config.get('REACT_APP_MATOMO_URL'),
                'REACT_APP_MATOMO_SITE_ID': config.get('REACT_APP_MATOMO_SITE_ID'),
                'REACT_APP_MATOMO_CONTAINER': config.get('REACT_APP_MATOMO_CONTAINER'),
            })
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options
        response.headers.setdefault('X-Frame-Options', 'DENY')
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Content-Type-Options
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
        # https://www.zaproxy.org/docs/alerts/10015/
        response.headers.setdefault('Cache-Control', 'no-cache, no-store, must-revalidate;')
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Pragma
        response.headers.setdefault('Pragma', 'no-cache')
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP
        response.headers.setdefault('Content-Security-Policy',
                                    ('default-src \'self\' \'unsafe-inline\' *.googleapis.com *.gov.bc.ca'
                                     ' *.gstatic.com;'
                                     ' script-src \'self\' \'unsafe-inline\' *.gov.bc.ca;'))
        return response
    except TemplateNotFound as exception:
        # This has most likely happened because there's nothing in the static folder
        # Make sure you've run npm build, and copied the static files into the correct location.
        logger.error(exception, exc_info=exception)


# This is the front end app. It's not going to do much other than serve up
# static files.
frontend = Starlette(routes=[
    Route('/', get_index),
    Mount('/', SPAStaticFiles(directory=get_static_foldername(), html=True), name='frontend')
])
