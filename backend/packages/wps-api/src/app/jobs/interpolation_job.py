"""
Job for running precipitation interpolation.

This job can be run manually or scheduled to interpolate station precipitation
observations to raster format using IDW.

Usage:
    python -m app.jobs.precipitation_interpolation "YYYY-MM-DD"
    python -m app.jobs.precipitation_interpolation  # Uses current date
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from typing import List

from aiohttp import ClientSession
from app.sfms.interpolation_processor import InterpolationProcessor
from app.sfms.interpolation_source import (
    StationInterpolationSource,
    StationPrecipitationSource,
    StationWindSpeedSource,
)
from app.sfms.sfms_common import fetch_station_actuals
from wps_shared.fuel_raster import find_latest_version
from wps_shared.stations import get_stations_from_source
from wps_shared.wildfire_one.wfwx_api import get_auth_header
from wps_shared.wps_logging import configure_logging
from wps_shared.rocketchat_notifications import send_rocketchat_notification
from wps_shared.utils.time import get_utc_now
from wps_shared.sfms.raster_addresser import RasterKeyAddresser
from wps_shared.utils.s3_client import S3Client

logger = logging.getLogger(__name__)


class InterpolationJob:
    """Job for processing weather parameter interpolation."""

    async def run(self, target_date: datetime) -> None:
        """
        Run interpolation for the specified date for weather parameters.

        :param target_date: The date to process (will use noon observation time)
        """
        logger.info("Starting interpolation job for %s", target_date.date())
        start_exec = get_utc_now()
        raster_addresser = RasterKeyAddresser()
        data_sources: List[StationInterpolationSource] = [
            StationPrecipitationSource(),
        ]

        try:
            # Create processor for target date (noon UTC hour 20)
            datetime_to_process = target_date.replace(hour=20, minute=0, second=0, microsecond=0)

            # Process precipitation interpolation
            processor = InterpolationProcessor(datetime_to_process, raster_addresser)

            async with S3Client() as s3_client:
                # Use a reference raster for grid properties
                # We'll use the fuel raster which defines the SFMS grid
                latest_version = await find_latest_version(
                    s3_client, raster_addresser, datetime_to_process, 1
                )
                fuel_raster_key = raster_addresser.get_fuel_raster_key(
                    target_date, version=latest_version
                )
                fuel_raster_path = raster_addresser.s3_prefix + "/" + fuel_raster_key
                logger.info("Using reference raster: %s", fuel_raster_path)

                # Fetch temperature observations from WF1
                async with ClientSession() as session:
                    auth_headers = await get_auth_header(session)
                    stations = await get_stations_from_source()
                    sfms_actuals = await fetch_station_actuals(
                        session, auth_headers, datetime_to_process, stations
                    )

                for data_source in data_sources:
                    s3_key = await processor.process(
                        s3_client,
                        fuel_raster_path,
                        sfms_actuals,
                        data_source,
                    )

                    # Calculate execution time
                    execution_time = get_utc_now() - start_exec
                    hours, remainder = divmod(execution_time.seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)

                    logger.info(
                        f"Interpolation completed successfully for ${data_source.weather_param.value}  -- "
                        "time elapsed %d hours, %d minutes, %.2f seconds",
                        hours,
                        minutes,
                        seconds,
                    )
                    logger.info("Output: %s", s3_key)

        except Exception as e:
            logger.error("Interpolation job failed", exc_info=e)
            rc_message = ":scream: Interpolation job failed"
            send_rocketchat_notification(rc_message, e)
            raise


def main():
    """Main entry point for the job."""
    if len(sys.argv) > 1:
        try:
            # Command-line arg as 'YYYY-MM-DD'
            target_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            logger.error("Error: Please provide the date in 'YYYY-MM-DD' format")
            sys.exit(1)
    else:
        # Default to current date
        target_date = get_utc_now()

    try:
        job = InterpolationJob()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(job.run(target_date))
    except Exception as e:
        logger.error(
            "An exception occurred while running precipitation interpolation job", exc_info=e
        )
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()
