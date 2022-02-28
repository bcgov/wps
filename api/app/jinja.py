import sys
import logging
from starlette.applications import Starlette
from starlette.routing import Route
from fastapi.requests import Request
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from app.frontend import get_static_foldername

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory=get_static_foldername())


async def get_jinja(request: Request):
    return templates.TemplateResponse("jinja.html", {'request': request, 'something': 'this is something'})

jinja = Starlette(routes=[
    Route('/', get_jinja),
])
