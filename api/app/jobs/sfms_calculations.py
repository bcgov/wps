import asyncio
import logging
import os
import sys

from app import configure_logging
from app.rocketchat_notifications import send_rocketchat_notification
from app.sfms.date_range_processor import BUIDateRangeProcessor
from app.sfms.raster_addresser import RasterKeyAddresser
from app.utils.time import get_utc_now

logger = logging.getLogger(__name__)

DAYS_TO_CALCULATE = 2


class SFMSCalcJob:
    async def calculate_bui(self):
        logger.info(f"Begin BUI raster calculations -- calculating {DAYS_TO_CALCULATE} days forward")

        start_time = get_utc_now()

        bui_processor = BUIDateRangeProcessor(start_time, DAYS_TO_CALCULATE, RasterKeyAddresser())
        await bui_processor.process_bui()

        # calculate the execution time.
        execution_time = get_utc_now() - start_time
        hours, remainder = divmod(execution_time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        logger.info(f"BUI processing finished -- time elapsed {hours} hours, {minutes} minutes, {seconds:.2f} seconds")


def main():
    try:
        job = SFMSCalcJob()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(job.calculate_bui())
    except Exception as e:
        logger.error("An exception occurred while processing DMC/DC/BUI raster calculations", exc_info=e)
        rc_message = ":scream: Encountered an error while processing RDPS data."
        send_rocketchat_notification(rc_message, e)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()
