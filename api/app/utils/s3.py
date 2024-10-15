"""Utils to help with s3"""

import logging
from typing import Generator, Tuple
from contextlib import asynccontextmanager
from aiobotocore.client import AioBaseClient
from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from osgeo import gdal
from app import config

logger = logging.getLogger(__name__)
BUCKET = config.get("OBJECT_STORE_BUCKET")


@asynccontextmanager
async def get_client() -> Generator[Tuple[AioBaseClient, str], None, None]:
    """Return AioBaseClient client and bucket"""
    server = config.get("OBJECT_STORE_SERVER")
    user_id = config.get("OBJECT_STORE_USER_ID")
    secret_key = config.get("OBJECT_STORE_SECRET")
    bucket = config.get("OBJECT_STORE_BUCKET")

    session = get_session()
    async with session.create_client("s3", endpoint_url=f"https://{server}", aws_secret_access_key=secret_key, aws_access_key_id=user_id) as client:
        try:
            yield client, bucket
        finally:
            del client


async def object_exists(client: AioBaseClient, bucket: str, target_path: str):
    """Check if and object exists in the object store"""
    # using list_objects, but could be using stat as well? don't know what's best.
    result = await client.list_objects_v2(Bucket=bucket, Prefix=target_path)
    contents = result.get("Contents", None)
    if contents:
        for content in contents:
            key = content.get("Key")
            if key == target_path:
                return True
    return False


async def object_exists_v2(target_path: str):
    """Check if and object exists in the object store"""
    async with get_client() as (client, bucket):
        return await object_exists(client, bucket, target_path)


async def all_objects_exist(*s3_keys: str):
    for key in s3_keys:
        key_exists = await object_exists_v2(key)
        if not key_exists:
            logger.error(f"{key} cannot be found in s3 bucket {BUCKET}")
            return False
    return True


async def read_into_memory(key: str):
    async with get_client() as (client, bucket):
        try:
            s3_source = await client.get_object(Bucket=bucket, Key=key)
            mem_path = f"/vsimem/{key}"
            s3_data = await s3_source["Body"].read()
            gdal.FileFromMemBuffer(mem_path, s3_data)
            data_source = gdal.Open(mem_path, gdal.GA_ReadOnly)
            gdal.Unlink(mem_path)
            data_band = data_source.GetRasterBand(1)
            data_geotransform = data_source.GetGeoTransform()
            data_projection = data_source.GetProjection()
            data_array = data_band.ReadAsArray()
            nodata_value = data_band.GetNoDataValue()
            data_source = None
            del data_source
            return (data_array, data_geotransform, data_projection, nodata_value)
        except ClientError as ex:
            if ex.response["Error"]["Code"] == "NoSuchKey":
                logger.info("No object found for key: %s", key)
                return (None, None, None)
            else:
                raise


def set_s3_gdal_config():
    gdal.SetConfigOption("AWS_SECRET_ACCESS_KEY", config.get("OBJECT_STORE_SECRET"))
    gdal.SetConfigOption("AWS_ACCESS_KEY_ID", config.get("OBJECT_STORE_USER_ID"))
    gdal.SetConfigOption("AWS_S3_ENDPOINT", config.get("OBJECT_STORE_SERVER"))
    gdal.SetConfigOption("AWS_VIRTUAL_HOSTING", "FALSE")
