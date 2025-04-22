"""Utils to help with s3"""

from datetime import datetime, timedelta, timezone
import logging
import re
from typing import Generator, Tuple
from contextlib import asynccontextmanager
from aiobotocore.client import AioBaseClient
from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from osgeo import gdal
from wps_shared import config

logger = logging.getLogger(__name__)


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


async def apply_retention_policy_on_date_folders(
    client: AioBaseClient,
    bucket: str,
    prefix: str,
    days_to_retain: int,
    dry_run: bool = False,
):
    """
    Applies a retention policy to an S3 bucket by deleting "folders" (prefixes) named by ISO date (YYYY-MM-DD).

    It deletes folders that are older than a specified number of days from today. Each folder is expected to be named
    as a date string, such as '2024-04-01/', and located under the given prefix (e.g., 'critical_hours/2024-04-01/').

    :param client: Asynchronous S3 client
    :param bucket: The name of the S3 bucket
    :param prefix: The prefix path within the bucket where date-named folders are located.
    :param days_to_retain: The number of most recent days to retain. Folders older than this will be deleted.
    :param dry_run: If True, no deletions will occur. Instead, actions will be logged to indicate what *would* be deleted.
                    Defaults to False.
    """
    date_pattern = re.compile(r"/(\d{4}-\d{2}-\d{2})/$")
    today = datetime.now(timezone.utc).date()
    retention_date = today - timedelta(days=days_to_retain)
    logger.info(f"Applying retention policy to '{prefix}'. Deleting data older than {days_to_retain} days (before {retention_date}).")

    res = await client.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter="/")

    if "CommonPrefixes" in res:
        for folder in res["CommonPrefixes"]:
            folder_prefix = folder["Prefix"]

            match = date_pattern.search(folder_prefix)
            if not match:
                logger.warning(f"Prefix '{folder_prefix}' does not contain a valid date.")
                continue

            folder_name = match.group(1)

            try:
                folder_date = datetime.strptime(folder_name, "%Y-%m-%d").date()
            except ValueError:
                logger.error(f"Failed to parse date from '{folder_name}' in prefix '{folder_prefix}'.")
                continue

            if folder_date < retention_date:
                res_objects = await client.list_objects_v2(Bucket=bucket, Prefix=folder_prefix)
                objects = res_objects.get("Contents", [])

                if not objects:
                    logger.info(f"No objects to delete in '{folder_prefix}'")
                    continue

                if dry_run:
                    logger.info(f"[Dry Run] Would delete {len(objects)} objects from '{folder_prefix}'")
                    continue

                else:
                    for obj in objects:
                        await client.delete_object(Bucket=bucket, Key=obj["Key"])
                    logger.info(f"Deleted {len(objects)} objects from '{folder_prefix}'")
