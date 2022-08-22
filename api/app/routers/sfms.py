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
    """
    Trigger the SFMS process to run. The idea is that some other process has placed the assets
    that are needed in the appropriate location, and then notifies us that we can start processing
    them.
    ```
    curl -X 'POST' \\
        'https://psu.nrs.gov.bc.ca/api/sfms/process' \\
        -H 'accept: application/json' \\
        -H 'Content-Type: application/json' \\
        -d '{
        "secret": "string"
    }'
    ```
    """
    if request.secret == config.get('SFMS_SECRET'):
        # TODO: Put message on queue to trigger processing of new HFI data.
        return Response(status_code=200)
    return Response(status_code=401)
