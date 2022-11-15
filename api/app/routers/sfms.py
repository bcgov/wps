""" Router for SFMS """
import io
import logging
from datetime import datetime, date
import os
from tempfile import SpooledTemporaryFile
from fastapi import APIRouter, UploadFile, Response, Request, BackgroundTasks
from app.nats import publish
from app.utils.s3 import get_client
from app import config
from app.auto_spatial_advisory.sfms import get_sfms_file_message, get_target_filename, get_date_part, is_hfi_file
from app.auto_spatial_advisory.nats import stream_name, subjects, sfms_file_subject
from app.schemas.auto_spatial_advisory import SFMSFile


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
                 request: Request,
                 background_tasks: BackgroundTasks):
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
    if not secret or secret != config.get('SFMS_SECRET'):
        return Response(status_code=401)
    # Get an async S3 client.
    async with get_client() as (client, bucket):
        # We save the Last-modified and Create-time as metadata in the object store - just
        # in case we need to know about it in the future.
        key = get_target_filename(file.filename)
        logger.info('Uploading file "%s" to "%s"', file.filename, key)
        meta_data = get_meta_data(request)
        await client.put_object(Bucket=bucket,
                                Key=key,
                                Body=FileLikeObject(file.file),
                                Metadata=meta_data)
        logger.info('Done uploading file')
    try:
        # We don't want to hold back the response to the client, so we'll publish the message
        # as a background task.
        # As noted below, the caller will have no idea if anything has gone wrong, which is
        # unfortunate, but we can't do anything about it.
        if is_hfi_file(filename=file.filename):
            logger.info("HFI file: %s, putting processing message on queue", file.filename)
            message = get_sfms_file_message(file.filename, meta_data)
            background_tasks.add_task(publish, stream_name, sfms_file_subject, message, subjects)
    except Exception as exception:  # pylint: disable=broad-except
        logger.error(exception, exc_info=True)
        # Regardless of what happens with putting a message on the queue, we return 200 to the
        # caller. The caller doesn't care that we failed to put a message on the queue. That's
        # our problem. We have the file, and it's up to us to make sure it gets processed now.
        # NOTE: Ideally, we'd be able to rely on the caller to retry the upload if we fail to
        # put a message on the queue. But, we can't do that because the caller isn't very smart,
        # and can't be given that level of responsibility.
    return Response(status_code=200)


@router.post('/manual')
async def upload_manual(file: UploadFile,
                        request: Request,
                        background_tasks: BackgroundTasks):
    """
    Trigger the SFMS process to run on the provided file.
    The header MUST include the SFMS secret key.

    ```
    curl -X 'POST' \\
        'https://psu.nrs.gov.bc.ca/api/sfms/upload' \\
        -H 'accept: application/json' \\
        -H 'Content-Type: multipart/form-data' \\
        -H 'Secret: secret' \\
        -H 'ForecastOrActual: actual' \\
        -H 'IssueDate: 2022-09-19' \\
        -F 'file=@hfi20220812.tif;type=image/tiff'
    ```
    """
    logger.info('sfms/manual')
    forecast_or_actual = request.headers.get('ForecastOrActual')
    issue_date = datetime.fromisoformat(str(request.headers.get('IssueDate')))
    secret = request.headers.get('Secret')
    if not secret or secret != config.get('SFMS_SECRET'):
        return Response(status_code=401)
    # Get an async S3 client.
    async with get_client() as (client, bucket):
        # We save the Last-modified and Create-time as metadata in the object store - just
        # in case we need to know about it in the future.
        key = os.path.join('sfms', 'uploads', forecast_or_actual, issue_date.isoformat()[:10], file.filename)
        # create the filename
        logger.info('Uploading file "%s" to "%s"', file.filename, key)
        meta_data = get_meta_data(request)
        await client.put_object(Bucket=bucket,
                                Key=key,
                                Body=FileLikeObject(file.file),
                                Metadata=meta_data)
        logger.info('Done uploading file')
    try:
        # We don't want to hold back the response to the client, so we'll publish the message
        # as a background task.
        # As noted below, the caller will have no idea if anything has gone wrong, which is
        # unfortunate, but we can't do anything about it.
        if is_hfi_file(filename=file.filename):
            logger.info("HFI file: %s, putting processing message on queue", file.filename)
            for_date = get_date_part(file.filename)
            message = SFMSFile(key=key,
                               run_type=forecast_or_actual,
                               last_modified=meta_data.get('last_modified'),
                               create_time=meta_data.get('create_time'),
                               run_date=issue_date,
                               for_date=date(year=int(for_date[0:4]),
                                             month=int(for_date[4:6]),
                                             day=int(for_date[6:8])))
            background_tasks.add_task(publish, stream_name, sfms_file_subject, message, subjects)
    except Exception as exception:  # pylint: disable=broad-except
        logger.error(exception, exc_info=True)
        # Regardless of what happens with putting a message on the queue, we return 200 to the
        # caller. The caller doesn't care that we failed to put a message on the queue. That's
        # our problem. We have the file, and it's up to us to make sure it gets processed now.
        # NOTE: Ideally, we'd be able to rely on the caller to retry the upload if we fail to
        # put a message on the queue. But, we can't do that because the caller isn't very smart,
        # and can't be given that level of responsibility.
    return Response(status_code=200)


@router.post('/manual/msgOnly')
async def upload_manual_msg(file: UploadFile,
                            request: Request,
                            background_tasks: BackgroundTasks):
    """
    Trigger the SFMS process to run on the provided file.
    The header MUST include the SFMS secret key.

    ```
    curl -X 'POST' \\
        'https://psu.nrs.gov.bc.ca/api/sfms/upload' \\
        -H 'accept: application/json' \\
        -H 'Content-Type: multipart/form-data' \\
        -H 'Secret: secret' \\
        -H 'ForecastOrActual: actual' \\
        -H 'IssueDate: 2022-09-19' \\
        -F 'file=@hfi20220812.tif;type=image/tiff'
    ```
    """
    logger.info('sfms/manual/msgOnly')
    forecast_or_actual = request.headers.get('ForecastOrActual')
    issue_date = datetime.fromisoformat(request.headers.get('IssueDate'))
    secret = request.headers.get('Secret')
    if not secret or secret != config.get('SFMS_SECRET'):
        return Response(status_code=401)
    try:
        key = os.path.join('sfms', 'uploads', forecast_or_actual, issue_date.isoformat()[:10], file.filename)
        meta_data = get_meta_data(request)
        if is_hfi_file(filename=file.filename):
            logger.info("HFI file: %s, putting processing message on queue", file.filename)
            for_date = get_date_part(file.filename)
            message = SFMSFile(key=key,
                               run_type=forecast_or_actual,
                               last_modified=meta_data.get('last_modified'),
                               create_time=meta_data.get('create_time'),
                               run_date=issue_date,
                               for_date=date(year=int(for_date[0:4]),
                                             month=int(for_date[4:6]),
                                             day=int(for_date[6:8])))
            background_tasks.add_task(publish, stream_name, sfms_file_subject, message, subjects)
    except Exception as exception:  # pylint: disable=broad-except
        logger.error(exception, exc_info=True)
        # Regardless of what happens with putting a message on the queue, we return 200 to the
        # caller. The caller doesn't care that we failed to put a message on the queue. That's
        # our problem. We have the file, and it's up to us to make sure it gets processed now.
        # NOTE: Ideally, we'd be able to rely on the caller to retry the upload if we fail to
        # put a message on the queue. But, we can't do that because the caller isn't very smart,
        # and can't be given that level of responsibility.
    return Response(status_code=200)
