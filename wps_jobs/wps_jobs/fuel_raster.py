"""
Job to update the fuel raster
"""

import argparse
from datetime import datetime
from osgeo import gdal
import asyncio
import logging
import os
import sys
from wps_shared import config
from wps_shared.wps_logging import configure_logging
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.rocketchat_notifications import send_rocketchat_notification
from wps_shared.sfms.raster_addresser import RasterKeyAddresser
from wps_shared.utils.s3_client import S3Client
from wps_shared.utils.time import get_utc_now
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.db.crud.fuel_layer import save_processed_fuel_raster
from wps_shared.db.models import FuelTypeRaster

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

    return current_version


async def start_job(
    raster_addresser: RasterKeyAddresser, start_datetime: datetime, unprocessed_object_name: str
):
    """
    This function performs the following steps:
    1. Finds the latest version of the fuel raster for the given start datetime.
    2. Copies the unprocessed raster object to a new key with an incremented version. The object already needs to exist in S3 storage at `sfms/static/`.
    3. Validates the content hash of the copied raster.
    4. If validation fails, deletes the new raster object and raises an error.
    5. If validation succeeds, extracts raster dimensions and saves metadata to the database.

    Args:
        raster_addresser (RasterKeyAddresser): An instance used to generate S3 keys for raster objects.
        start_datetime (datetime): The datetime associated with the raster job.
        unprocessed_object_name (str): The S3 object name of the unprocessed raster.
        expected_hash (str): The expected content hash of the raster file for validation.

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
            async with get_async_write_session_scope() as db_session:
                now = get_utc_now()
                await save_processed_fuel_raster(
                    db_session,
                    FuelTypeRaster(
                        year=start_datetime.year,
                        version=new_version,
                        xsize=xsize,
                        ysize=ysize,
                        object_store_path=new_key,
                        content_hash=expected_hash,
                        create_timestamp=now,
                    ),
                )


def main():
    """Kicks off asynchronous processing of new fuel raster"""
    parser = argparse.ArgumentParser(
        description="Retrieve and store the latest fuel raster by date"
    )
    parser.add_argument(
        "-d", "--date", default=None, help="The date to use for looking up the fuel raster."
    )
    parser.add_argument(
        "-k", "--key", default=None, help="Object storage key that points to the unprocessed raster"
    )

    args, _ = parser.parse_known_args()
    start_datetime = datetime.fromisoformat(args.date) if args.date else get_utc_now()
    unprocessed_object_name = str(args.key) if args.key else config.get("FUEL_RASTER_NAME")
    try:
        # We don't want gdal to silently swallow errors.
        gdal.UseExceptions()
        logger.debug("Begin processing new fuel raster.")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            start_job(RasterKeyAddresser(), start_datetime, unprocessed_object_name)
        )

        # Exit with 0 - success.
        sys.exit(os.EX_OK)
    except Exception as exception:
        # Exit non 0 - failure.
        logger.error("An error occurred while processing fuel raster.", exc_info=exception)
        rc_message = ":scream: Encountered an error while processing fuel raster."
        send_rocketchat_notification(rc_message, exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()
