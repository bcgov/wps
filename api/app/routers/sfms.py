""" Router for SFMS """
import os
import io
import logging
from datetime import datetime, date
from tempfile import SpooledTemporaryFile
from fastapi import APIRouter, UploadFile, Response, Request
from app.utils.s3 import get_client
from app import config
from app.utils.time import get_hour_20, get_utc_now, get_pst_now

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/sfms",
)


class FileLikeObject(io.IOBase):
    """ Very basic wrapper of the SpooledTemporaryFile to expose the file-like object interface.

    The aiobotocore library expects a file-like object, but we can't pass the SpooledTemporaryFile
    object directly to aiobotocore. aiobotocore looks for a "tell" method, which isn't present
    on SpooledTemporaryFile. aiobotocore doesn't need an object with a tell method, and understands
    how to use IOBase, so we can wrap the SpooledTemporaryFile in a class that implements IOBase
    to make aiobotocore happy.
    """

    def __init__(self, file: SpooledTemporaryFile):
        super().__init__()
        self.file = file

    def read(self, size: int = -1):
        return self.file.read(size)

    def write(self, b: bytes):  # pylint: disable=invalid-name
        return self.file.write(b)

    def seek(self, offset: int, whence: int = io.SEEK_SET):
        return self.file.seek(offset, whence)


def is_actual(filename: str) -> bool:
    """ Decide whether the file is an actual or forecast file.
    08h00 PST on the 22nd hfi20220823.tif -> forecast
    13h00 PST on the 22nd hfi20220823.tif -> forecast
    08h00 PST on the 23rd hfi20220823.tif -> forecast
    13h00 PST on the 23rd hfi20220823.tif -> actual
    """
    file_date_string = filename[-12:-4]
    file_date = date(
        year=int(file_date_string[:4]),
        month=int(file_date_string[4:6]),
        day=int(file_date_string[6:8]))
    now = get_pst_now()
    now_date = now.date()

    if file_date < now_date:
        # It's from the past - it's an actual.
        return True
    elif file_date > now_date:
        # It's from the future - it's a forecast.
        return False
    # It's from today - now it get's weird.
    # If the current time is after solar noon, it's an actual.
    # If the current time is before solar noon, it's a forecast.
    solar_noon_today = get_hour_20(now)
    return now > solar_noon_today


def get_prefix(filename: str) -> str:
    if is_actual(filename):
        return 'actual'
    return 'forecast'


def get_target_filename(filename: str) -> str:
    """ Get the target filename, something that looks like this:
    bucket/sfms/upload/forecast/[issue date NOT TIME]/hfi20220823.tif
    bucket/sfms/upload/actual/[issue date NOT TIME]/hfi20220823.tif
    """
    # We are assuming that the local server time, matches the issue date. We assume that
    # right after a file is generated, this API is called - and as such the current
    # time IS the issue date.
    issue_date = get_utc_now()
    # depending on the issue date, we decide if it's a forecast or actual.
    prefix = get_prefix(filename)
    # create the filename
    return os.path.join('sfms', 'uploads', prefix, issue_date.isoformat()[:10], filename)


def get_meta_data(request: Request) -> dict:
    """ Create the meta-data for the s3 object.
    # NOTE: No idea what timezone this is going to be. Is it UTC? Is it PST? Is it PDT?
    """
    last_modified = datetime.fromisoformat(request.headers.get(
        'Last-modified'))
    create_time = datetime.fromisoformat(request.headers.get(
        'Create-time'))
    return {
        'last_modified': last_modified.isoformat(),
        'create_time': create_time.isoformat()}


@router.post('/upload')
async def upload(file: UploadFile,
                 request: Request):
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
        # We save the Last-modified and Create-time as metadata in the object store - just
        # in case we need to know about it in the future.
        key = get_target_filename(file.filename)
        logger.info('Uploading file "%s" to "%s"', file.filename, key)
        await client.put_object(Bucket=bucket, Key=key, Body=FileLikeObject(file.file),
                                Metadata=get_meta_data(request))
        logger.info('Done uploading file')
        # TODO: Put message on queue to trigger processing of new HFI data.
        return Response(status_code=200)
