import os
import logging
from aiobotocore.session import get_session
from types_aiobotocore_s3.client import S3Client
from datetime import date
from decouple import config


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


def get_hfi_objects(objects):
    if objects is None:
        return []
    tif_objects = list(filter(lambda obj: obj["Key"].endswith('tif')
                              or obj["Key"].endswith('tiff'), objects))
    logger.info("Retrieved tifs: %s", tif_objects)
    hfi_tif_objects = list(filter(lambda obj: os.path.basename(obj["Key"]).startswith('hfi'), tif_objects))
    logger.info("Retrieved hfi tifs: %s", hfi_tif_objects)
    return hfi_tif_objects


async def get_tifs_for_date(current_date: date):

    forecast_path = os.path.join('sfms', 'uploads', 'forecast', current_date.isoformat())
    actual_path = os.path.join('sfms', 'uploads', 'actual', current_date.isoformat())

    server = config('OBJECT_STORE_SERVER')
    user_id = config('OBJECT_STORE_USER_ID')
    secret_key = config('OBJECT_STORE_SECRET')
    bucket = config('OBJECT_STORE_BUCKET')

    logger.info(bucket)
    logger.info(forecast_path)

    session = get_session()
    async with session.create_client('s3',
                                     endpoint_url=f'https://{server}',
                                     aws_secret_access_key=secret_key,
                                     aws_access_key_id=user_id) as client:
        client: S3Client
        forecast_result = await client.list_objects_v2(Bucket=bucket,
                                                       Prefix=forecast_path)
        forecast_contents = forecast_result.get('Contents', None)
        forecast_objects = get_hfi_objects(forecast_contents)

        actual_result = await client.list_objects_v2(Bucket=bucket,
                                                     Prefix=actual_path)
        actual_contents = actual_result.get('Contents', None)
        actual_objects = get_hfi_objects(actual_contents)

        return forecast_objects + actual_objects
