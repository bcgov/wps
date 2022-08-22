""" Router for SFMS """
import logging
from fastapi import APIRouter, Response
from app.schemas.sfms import ProcessRequest
from app import config

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/sfms",
)


@router.post('/process')
def process(request: ProcessRequest):
    """ Process a request """
    if request.secret == config.get('SFMS_SECRET'):
        # TODO: Put message on queue to trigger processing of new HFI data.
        return Response(status_code=200)
    return Response(status_code=401)
