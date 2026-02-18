"""
Update the fuel raster
"""

import logging
from datetime import datetime

from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.sfms.raster_addresser import RasterKeyAddresser
from wps_shared.utils.s3_client import S3Client
from wps_shared.utils.time import get_utc_now

logger = logging.getLogger(__name__)


async def find_latest_version(
    s3_client: S3Client, raster_addresser: RasterKeyAddresser, now: datetime, version: int
):
    current_version = version
    key = raster_addresser.get_fuel_raster_key(now, current_version)
    exists = await s3_client.all_objects_exist(key)
    while exists:
        current_version += 1
        key = raster_addresser.get_fuel_raster_key(now, current_version)
        exists = await s3_client.all_objects_exist(key)
        if not exists:
            current_version -= 1

    return current_version


MAX_FALLBACK_YEARS = 5


async def find_latest_fuel_raster_key(
    s3_client: S3Client, raster_addresser: RasterKeyAddresser, now: datetime
) -> str:
    """Find the latest fuel raster key, falling back to previous years if the current year has none.

    :param s3_client: S3Client instance
    :param raster_addresser: RasterKeyAddresser instance
    :param now: current UTC datetime
    :return: S3 key to the latest fuel raster
    :raises RuntimeError: if no fuel raster is found within MAX_FALLBACK_YEARS
    """
    for year_offset in range(MAX_FALLBACK_YEARS):
        current_date = now.replace(year=now.year - year_offset)
        version = await find_latest_version(s3_client, raster_addresser, current_date, 1)
        key = raster_addresser.get_fuel_raster_key(current_date, version)
        if await s3_client.all_objects_exist(key):
            if year_offset > 0:
                logger.warning(
                    "No fuel raster for %d, falling back to %d v%d",
                    now.year,
                    current_date.year,
                    version,
                )
            return key

    raise RuntimeError(f"No fuel raster found within the last {MAX_FALLBACK_YEARS} years")


async def process_fuel_type_raster(
    raster_addresser: RasterKeyAddresser, start_datetime: datetime, unprocessed_object_name: str
):
    """
    This function performs the following steps:
    1. Finds the latest version of the fuel raster for the given start datetime.
    2. Copies the unprocessed raster object to a new key with an incremented version. The object already needs to exist in S3 storage at `sfms/static/`.
    3. Validates the content hash of the copied raster.
    4. If validation fails, deletes the new raster object and raises an error.
    5. If validation succeeds, extracts raster dimensions and returns metadata to the caller.

    Args:
        raster_addresser (RasterKeyAddresser): An instance used to generate S3 keys for raster objects.
        start_datetime (datetime): The datetime associated with the raster job.
        unprocessed_object_name (str): The S3 object name of the unprocessed raster.

    Raises:
        ValueError: If the content hash validation fails or the raster cannot be stored.
    """
    async with S3Client() as s3_client:
        current_version = await find_latest_version(
            s3_client, RasterKeyAddresser(), start_datetime, 1
        )
        new_version = current_version + 1
        unprocessed_key = raster_addresser.get_unprocessed_fuel_raster_key(unprocessed_object_name)
        new_key = raster_addresser.get_fuel_raster_key(start_datetime, new_version)

        try:
            expected_hash = await s3_client.get_content_hash(unprocessed_key)
            await s3_client.copy_object(unprocessed_key, new_key)
            res = await s3_client.get_fuel_raster(new_key, expected_hash)
        except ValueError as e:
            logger.error(f"Could not store fuel raster at: {new_key}", exc_info=e)
            await s3_client.delete_object(new_key)
            raise e

        logger.info("Raster file content hash succeeded")
        with WPSDataset.from_bytes(res) as new_raster_ds:
            xsize = new_raster_ds.as_gdal_ds().RasterXSize
            ysize = new_raster_ds.as_gdal_ds().RasterYSize
        now = get_utc_now()
        return (start_datetime.year, new_version, xsize, ysize, new_key, expected_hash, now)
