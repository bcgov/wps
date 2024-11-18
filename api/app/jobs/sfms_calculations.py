import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

from app import configure_logging
from app.geospatial.wps_dataset import multi_wps_dataset_context
from app.rocketchat_notifications import send_rocketchat_notification
from app.sfms.daily_fwi_processor import DailyFWIProcessor
from app.sfms.raster_addresser import RasterKeyAddresser
from app.utils.s3_client import S3Client
from app.utils.time import get_utc_now

logger = logging.getLogger(__name__)

DAYS_TO_CALCULATE = 2


class SFMSCalcJob:
    async def calculate_daily_fwi(self, start_time: datetime):
        """
        Entry point for processing SFMS DMC/DC/BUI rasters. To run from a specific date manually in openshift,
        see openshift/sfms-calculate/README.md
        """
        logger.info(f"Begin BUI raster calculations -- calculating {DAYS_TO_CALCULATE} days forward")

        start_exec = get_utc_now()

        daily_processor = DailyFWIProcessor(start_time, DAYS_TO_CALCULATE, RasterKeyAddresser())

        async with S3Client() as s3_client:
            await daily_processor.process(s3_client, multi_wps_dataset_context, multi_wps_dataset_context, multi_wps_dataset_context)

        # calculate the execution time.
        execution_time = get_utc_now() - start_exec
        hours, remainder = divmod(execution_time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        logger.info(f"Daily FWI processing finished -- time elapsed {hours} hours, {minutes} minutes, {seconds:.2f} seconds")


def main():
    if len(sys.argv) > 1:
        try:
            # command-line arg as 'YYYY-MM-DD HH'
            start_time = datetime.strptime(sys.argv[1], "%Y-%m-%d %H").replace(tzinfo=timezone.utc)
        except ValueError:
            logger.error("Error: Please provide the date and hour in 'YYYY-MM-DD HH' format (as a single string)")
            sys.exit(1)
    else:
        # default to the current datetime
        start_time = get_utc_now()
    try:
        job = SFMSCalcJob()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(job.calculate_daily_fwi(start_time))
    except Exception as e:
        logger.error("An exception occurred while processing SFMS raster calculations", exc_info=e)
        rc_message = ":scream: Encountered an error while processing SFMS raster data."
        send_rocketchat_notification(rc_message, e)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()
