""" Router for SFMS """
import io
import logging
from datetime import datetime, date
import os
from tempfile import SpooledTemporaryFile
from fastapi import APIRouter, UploadFile, Response, Request, BackgroundTasks, Depends, Header
from app.auth import sfms_authenticate
from app.nats_publish import publish
from app.schemas.sfms import HourlyTIF, HourlyTIFs
from app.utils.s3 import get_client
from app import config
from app.auto_spatial_advisory.sfms import get_hourly_filename, get_sfms_file_message, get_target_filename, get_date_part, is_ffmc_file, is_hfi_file
from app.auto_spatial_advisory.nats_config import stream_name, subjects, sfms_file_subject
from app.schemas.auto_spatial_advisory import ManualSFMS, SFMSFile


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/sfms",
)

SFMS_HOURLIES_PERMISSIONS = 'public-read'

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

    def write(self, b: bytes):
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

@router.get('/ready')
async def get_ready():
    """ A simple endpoint for OpenShift readiness """
    return Response()


@router.get('/health')
async def get_health():
    """ A simple endpoint for Openshift Healthchecks. """
    return Response()


@router.post('/upload')
async def upload(file: UploadFile,
                 request: Request,
                 background_tasks: BackgroundTasks,
                 _=Depends(sfms_authenticate)):
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
        await file.close()
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
    except Exception as exception:
        logger.error(exception, exc_info=True)
        # Regardless of what happens with putting a message on the queue, we return 200 to the
        # caller. The caller doesn't care that we failed to put a message on the queue. That's
        # our problem. We have the file, and it's up to us to make sure it gets processed now.
        # NOTE: Ideally, we'd be able to rely on the caller to retry the upload if we fail to
        # put a message on the queue. But, we can't do that because the caller isn't very smart,
        # and can't be given that level of responsibility.
    return Response(status_code=200)

@router.post('/upload/hourlies')
async def upload_hourlies(file: UploadFile,
                 request: Request,
                 _=Depends(sfms_authenticate)):
    """
    Trigger the SFMS process to run on the provided file for hourlies.
    The header MUST include the SFMS secret key.

    ```
    curl -X 'POST' \\
        'https://psu.nrs.gov.bc.ca/api/sfms/upload/hourlies' \\
        -H 'accept: application/json' \\
        -H 'Content-Type: multipart/form-data' \\
        -H 'Secret: secret' \\
        -F 'file=@hfi20220812.tif;type=image/tiff'
    ```
    """
    logger.info('sfms/upload/hourlies')

    if is_ffmc_file(file.filename):
        # Get an async S3 client.
        async with get_client() as (client, bucket):
            # We save the Last-modified and Create-time as metadata in the object store - just
            # in case we need to know about it in the future.
            key = get_hourly_filename(file.filename)
            logger.info('Uploading file "%s" to "%s"', file.filename, key)
            meta_data = get_meta_data(request)
            await client.put_object(Bucket=bucket,
                                    Key=key,
                                    ACL=SFMS_HOURLIES_PERMISSIONS,
                                    Body=FileLikeObject(file.file),
                                    Metadata=meta_data)
            await file.close()
            logger.info('Done uploading file')
    return Response(status_code=200)


@router.get('/hourlies', response_model=HourlyTIFs)
async def get_hourlies(for_date: date):
    """
    Retrieve hourly FFMC TIF files for the given date. 
    Files are named in the format: "fine_fuel_moisture_codeYYYYMMDDHH.tif", where HH is the two digit day hour in PST.
    """
    logger.info('sfms/hourlies')

    async with get_client() as (client, bucket):
        logger.info('Retrieving hourlies for "%s"', for_date)
        bucket = config.get('OBJECT_STORE_BUCKET')
        response = await client.list_objects_v2(Bucket=bucket, Prefix=f'sfms/uploads/hourlies/{str(for_date)}')
        if 'Contents' in response:
            hourlies = [HourlyTIF(url=f'https://nrs.objectstore.gov.bc.ca/{bucket}/{hourly["Key"]}') for hourly in response['Contents']]
            logger.info(f'Retrieved {len(hourlies)} hourlies')
            return HourlyTIFs(hourlies=hourlies)
        logger.info(f'No hourlies found for {for_date}')
        return HourlyTIFs(hourlies=[])
        

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
        await file.close()
        logger.info('Done uploading file')
    return add_msg_to_queue(file, key, forecast_or_actual, meta_data, issue_date, background_tasks)


def add_msg_to_queue(file: UploadFile, key: str, forecast_or_actual: str, meta_data: dict,
                     issue_date: datetime, background_tasks: BackgroundTasks):
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
                               last_modified=datetime.fromisoformat(meta_data.get('last_modified')),
                               create_time=datetime.fromisoformat(meta_data.get('create_time')),
                               run_date=issue_date,
                               for_date=date(year=int(for_date[0:4]),
                                             month=int(for_date[4:6]),
                                             day=int(for_date[6:8])))
            background_tasks.add_task(publish, stream_name, sfms_file_subject, message, subjects)
    except Exception as exception:
        logger.error(exception, exc_info=True)
        # Regardless of what happens with putting a message on the queue, we return 200 to the
        # caller. The caller doesn't care that we failed to put a message on the queue. That's
        # our problem. We have the file, and it's up to us to make sure it gets processed now.
        # NOTE: Ideally, we'd be able to rely on the caller to retry the upload if we fail to
        # put a message on the queue. But, we can't do that because the caller isn't very smart,
        # and can't be given that level of responsibility.
    return Response(status_code=200)


@router.post('/manual/msgOnly')
async def upload_manual_msg(message: ManualSFMS,
                            background_tasks: BackgroundTasks,
                            secret: str | None = Header(default=None)):
    """
    Trigger the SFMS process to run on a tif file that already exists in s3.
    Client provides, key, for_date, runtype, run_date and an
    SFMS message is queued up on the message queue.
    """
    logger.info('sfms/manual/msgOnly')
    logger.info("Received request to process tif: %s", message.key)
    if not secret or secret != config.get('SFMS_SECRET'):
        return Response(status_code=401)

    async with get_client() as (client, bucket):
        tif_object = await client.get_object(Bucket=bucket,
                                             Key=message.key)
        logger.info('Found requested object: %s', tif_object)
        last_modified = datetime.fromisoformat(tif_object["Metadata"]["last_modified"])
        create_time = datetime.fromisoformat(tif_object["Metadata"]["create_time"])
        message = SFMSFile(key=message.key,
                           run_type=message.runtype,
                           last_modified=last_modified,
                           create_time=create_time,
                           run_date=message.run_date,
                           for_date=message.for_date)
    background_tasks.add_task(publish, stream_name, sfms_file_subject, message, subjects)
