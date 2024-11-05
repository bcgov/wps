import asyncio
from datetime import datetime, timezone
import logging
import os
import sys

from app import configure_logging
from app.rocketchat_notifications import send_rocketchat_notification
from app.sfms.date_range_processor import BUIDateRangeProcessor
from app.sfms.raster_addresser import RasterKeyAddresser
from app.utils.s3_client import S3Client
from app.utils.time import get_utc_now
from app.geospatial.wps_dataset import multi_wps_dataset_context


logger = logging.getLogger(__name__)

DAYS_TO_CALCULATE = 2


class SFMSCalcJob:
    async def calculate_bui(self, start_time: datetime):
        logger.info(f"Begin BUI raster calculations -- calculating {DAYS_TO_CALCULATE} days forward")

        bui_processor = BUIDateRangeProcessor(start_time, DAYS_TO_CALCULATE, RasterKeyAddresser())

        async with S3Client() as s3_client:
            await bui_processor.process_bui(s3_client, multi_wps_dataset_context, multi_wps_dataset_context)

        # calculate the execution time.
        execution_time = get_utc_now() - start_time
        hours, remainder = divmod(execution_time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        logger.info(f"BUI processing finished -- time elapsed {hours} hours, {minutes} minutes, {seconds:.2f} seconds")


def main():
    if len(sys.argv) > 1:
        try:
            # command-line arg as 'YYYY-MM-DD HH'
            start_time = datetime.strptime(sys.argv[1], "%Y-%m-%d %H").replace(tzinfo=timezone.utc)
        except ValueError:
            print("Error: Please provide the date and hour in 'YYYY-MM-DD HH' format (as a single string)")
            sys.exit(1)
    else:
        # default to the current datetime
        start_time = get_utc_now()
    try:
        job = SFMSCalcJob()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(job.calculate_bui(start_time))
    except Exception as e:
        logger.error("An exception occurred while processing DMC/DC/BUI raster calculations", exc_info=e)
        rc_message = ":scream: Encountered an error while processing SFMS raster data."
        send_rocketchat_notification(rc_message, e)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()
