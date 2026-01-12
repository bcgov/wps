"""
Job for running temperature interpolation.

This job can be run manually or scheduled to interpolate station temperature
observations to raster format using IDW and elevation adjustment.

Usage:
    python -m app.jobs.temperature_interpolation "YYYY-MM-DD"
    python -m app.jobs.temperature_interpolation  # Uses current date
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from wps_shared.wps_logging import configure_logging
from wps_shared.rocketchat_notifications import send_rocketchat_notification
from wps_shared.utils.time import get_utc_now
from wps_shared.sfms.raster_addresser import RasterKeyAddresser
from wps_shared.utils.s3_client import S3Client
from app.sfms.temperature_interpolation_processor import TemperatureInterpolationProcessor

logger = logging.getLogger(__name__)


class TemperatureInterpolationJob:
    """Job for processing temperature interpolation."""

    async def run(self, target_date: datetime) -> None:
        """
        Run temperature interpolation for the specified date.

        :param target_date: The date to process (will use noon observation time)
        """
        logger.info("Starting temperature interpolation job for %s", target_date.date())
        start_exec = get_utc_now()

        try:
            # Create processor for target date (noon UTC hour 20)
            datetime_to_process = target_date.replace(hour=20, minute=0, second=0, microsecond=0)

            # Use a reference raster for grid properties
            # We'll use the fuel raster which defines the SFMS grid
            raster_addresser = RasterKeyAddresser()
            fuel_raster_key = raster_addresser.get_fuel_raster_key(target_date, version=2025)
            fuel_raster_path = raster_addresser.s3_prefix + "/" + fuel_raster_key

            logger.info("Using reference raster: %s", fuel_raster_path)

            # Process temperature interpolation
            processor = TemperatureInterpolationProcessor(datetime_to_process)

            async with S3Client() as s3_client:
                s3_key = await processor.process(s3_client, fuel_raster_path)

            # Calculate execution time
            execution_time = get_utc_now() - start_exec
            hours, remainder = divmod(execution_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            logger.info(
                "Temperature interpolation completed successfully -- "
                "time elapsed %d hours, %d minutes, %.2f seconds",
                hours, minutes, seconds
            )
            logger.info("Output: %s", s3_key)

        except Exception as e:
            logger.error("Temperature interpolation job failed", exc_info=e)
            rc_message = ":scream: Temperature interpolation job failed"
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
        job = TemperatureInterpolationJob()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(job.run(target_date))
    except Exception as e:
        logger.error("An exception occurred while running temperature interpolation job", exc_info=e)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()
