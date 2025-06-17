"""
Job to update the fuel raster
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime

from osgeo import gdal

from wps_shared import config
from wps_shared.auto_spatial_advisory.fuel_raster import process_fuel_type_raster
from wps_shared.db.crud.fuel_layer import save_processed_fuel_raster
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models import FuelTypeRaster
from wps_shared.rocketchat_notifications import send_rocketchat_notification
from wps_shared.sfms.raster_addresser import RasterKeyAddresser
from wps_shared.utils.time import get_utc_now
from wps_shared.wps_logging import configure_logging

logger = logging.getLogger(__name__)


async def start_job(
    raster_addresser: RasterKeyAddresser, start_datetime: datetime, unprocessed_object_name: str
):
    (
        year,
        version,
        xsize,
        ysize,
        object_store_path,
        content_hash,
        create_timestamp,
    ) = process_fuel_type_raster(raster_addresser, start_datetime, unprocessed_object_name)
    async with get_async_write_session_scope() as db_session:
        await save_processed_fuel_raster(
            db_session,
            FuelTypeRaster(
                year=year,
                version=version,
                xsize=xsize,
                ysize=ysize,
                object_store_path=object_store_path,
                content_hash=content_hash,
                create_timestamp=create_timestamp,
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
