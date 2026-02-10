"""Utils to help with s3"""

from datetime import date, datetime, timedelta, timezone
import logging
from typing import AsyncGenerator, Optional, Tuple
from contextlib import asynccontextmanager
from aiobotocore.client import AioBaseClient
from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from osgeo import gdal
from wps_shared import config
from wps_shared.utils.s3_client import S3Client
from wps_shared.utils.time import get_utc_now

logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_client() -> AsyncGenerator[Tuple[AioBaseClient, str], None]:
    """Return AioBaseClient client and bucket"""
    server = config.get("OBJECT_STORE_SERVER")
    user_id = config.get("OBJECT_STORE_USER_ID")
    secret_key = config.get("OBJECT_STORE_SECRET")
    bucket = config.get("OBJECT_STORE_BUCKET")

    session = get_session()
    async with session.create_client(
        "s3",
        endpoint_url=f"https://{server}",
        aws_secret_access_key=secret_key,
        aws_access_key_id=user_id,
    ) as client:
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
            data_source = None
            del data_source
            return (data_array, data_geotransform, data_projection)
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
    # Enable temp file usage for COG creation to S3 (COG driver requires random write access)
    gdal.SetConfigOption("CPL_VSIL_USE_TEMP_FILE_FOR_RANDOM_WRITE", "YES")
    # Set temp directory to /tmp for GDAL temp files (e.g., .ovr.tmp during COG creation)
    gdal.SetConfigOption("CPL_TMPDIR", "/tmp")


def extract_date_from_prefix(folder_prefix: str, base_prefix: str) -> Optional[date]:
    folder_name = folder_prefix.removeprefix(base_prefix).strip("/").split("/")[0]

    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(folder_name, fmt).date()
        except ValueError:
            pass

    logger.warning(f"Failed to parse date from '{folder_name}' in prefix '{folder_prefix}'.")
    return None


async def apply_retention_policy_on_date_folders(
    client: S3Client,
    prefix: str,
    days_to_retain: int,
    dry_run: bool = False,
):
    if not prefix.endswith("/"):
        prefix += "/"

    today = get_utc_now().date()
    retention_date = today - timedelta(days=days_to_retain)

    logger.info(
        "Applying retention policy to '%s'. Deleting data before %s.",
        prefix,
        retention_date,
    )

    async for folder_prefix in client.iter_common_prefixes(prefix):
        folder_date = extract_date_from_prefix(folder_prefix, prefix)
        if not folder_date or folder_date >= retention_date:
            continue

        count = await client.delete_prefix(folder_prefix, dry_run=dry_run)

        if count == 0:
            logger.info("No objects to delete in '%s'", folder_prefix)
        else:
            logger.info(
                "%s %d objects from '%s'",
                "Would delete" if dry_run else "Deleted",
                count,
                folder_prefix,
            )
