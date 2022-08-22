""" Router for SFMS """
import os
import io
import logging
from datetime import datetime
from tempfile import SpooledTemporaryFile
from fastapi import APIRouter, UploadFile, Response, Request
from app.utils.s3 import get_client
from app import config

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/sfms",
)


class FileLikeObject(io.IOBase):
    """ Very basic wrapper of the SpooledTemporaryFile to expose the file-like object interface. """

    def __init__(self, file: SpooledTemporaryFile):
        self.file = file

    def read(self, size: int = -1):
        return self.file.read(size)

    def write(self, b: bytes):
        return self.file.write(b)

    def seek(self, offset: int, whence: int = io.SEEK_SET):
        return self.file.seek(offset, whence)


@router.post('/upload')
async def upload(file: UploadFile, request: Request):
    """
    Trigger the SFMS process to run on the provided file.
    The header MUST include the SFMS secret key.

    ```
    curl -X 'POST' \\
        'https://psu.nrs.gov.bc.ca/api/sfms/upload' \\
        -H 'accept: application/json' \\
        -H 'Content-Type: multipart/form-data' \\
        -H 'Secret: secret' \\
        -F 'file=@hfi20220812.tif;type=image/tiff'
    ```
    """
    logger.info('sfms/upload/')
    secret = request.headers.get('Secret')
    if secret != config.get('SFMS_SECRET'):
        return Response(status_code=401)
    # Get an async S3 client.
    async with get_client() as (client, bucket):
        key = os.path.join('sfms', 'uploads', datetime.now().isoformat(), file.filename)
        logger.info('Uploading file "%s" to "%s"', file.filename, key)
        await client.put_object(Bucket=bucket, Key=key, Body=FileLikeObject(file.file))
        logger.info('Done uploading file')
        # TODO: Put message on queue to trigger processing of new HFI data.
        return Response(status_code=200)
