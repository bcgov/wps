""" Serve up the Single Page Application
"""
import os
from starlette.applications import Starlette
from starlette.types import Scope
from starlette.routing import Route, Mount
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
from app import config


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
        # If file not found, try to serve up the root.
        if response.status_code == 404:
            response = await super().get_response('.', scope)
        return response


def get_static_foldername():
    """ Get the static foldername - it defaults to 'static', but can be changed by setting
    an environment variable.
    """
    dirname = os.path.dirname(os.path.abspath(__file__))
    static_foldername = config.get('STATIC_FOLDER', os.path.join(dirname, '../', 'static'))
    return static_foldername


templates = Jinja2Templates(directory=get_static_foldername())


async def get_config(request: Request):
    """ Apply jinja template response to config.js
    """
    return templates.TemplateResponse(
        "config.js",
        {
            'request': request,
            'PUBLIC_URL': config.get('PUBLIC_URL', '.'),
            'REACT_APP_KEYCLOAK_AUTH_URL': config.get('REACT_APP_KEYCLOAK_AUTH_URL'),
            'REACT_APP_KEYCLOAK_REALM': config.get('REACT_APP_KEYCLOAK_REALM'),
            'REACT_APP_KEYCLOAK_CLIENT': config.get('REACT_APP_KEYCLOAK_CLIENT'),
            'REACT_APP_FIDER_LINK': config.get('REACT_APP_FIDER_LINK')
        })


async def get_index(request: Request):
    """ Apply jina template to index.html
    """
    return templates.TemplateResponse(
        "index.html",
        {
            'request': request,
            'PUBLIC_URL': config.get('PUBLIC_URL', '.'),
            'REACT_APP_KEYCLOAK_AUTH_URL': config.get('REACT_APP_KEYCLOAK_AUTH_URL'),
            'REACT_APP_MATOMO_URL': config.get('REACT_APP_MATOMO_URL'),
            'REACT_APP_MATOMO_SITE_ID': config.get('REACT_APP_MATOMO_SITE_ID'),
            'REACT_APP_MATOMO_CONTAINER': config.get('REACT_APP_MATOMO_CONTAINER'),
        })


# This is the front end app. It's not going to do much other than serve up
# static files.
# TODO - modify SPAStaticFiles to always apply template to root
frontend = Starlette(routes=[
    Route('/config.js', get_config),
    Route('/index.html', get_index),
    Route('/', get_index),
    Route('/morecast', get_index),
    Route('/percentile-calculator', get_index),
    Route('/fire-weather', get_index),
    Mount('/', SPAStaticFiles(directory=get_static_foldername(), html=True), name='frontend')
])
