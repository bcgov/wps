import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

from wps_shared.rocketchat_notifications import send_rocketchat_notification
from wps_shared.utils.time import get_utc_now
from wps_shared.wps_logging import configure_logging

from app.fire_watch.calculate_weather import process_all_fire_watch_weather

logger = logging.getLogger(__name__)


async def main():
    if len(sys.argv) > 1:
        try:
            # command-line arg as 'YYYY-MM-DD'
            start_datetime = datetime.strptime(sys.argv[1], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            logger.error("Error: Please provide the date and hour in 'YYYY-MM-DD' format (as a single string)")
            sys.exit(1)
    else:
        start_datetime = get_utc_now()

    try:
        await process_all_fire_watch_weather(start_datetime)
    except Exception as e:
        logger.error("An exception occurred while processing fire watch weather data", exc_info=e)
        rc_message = ":scream: Encountered an error while processing fire watch weather data."
        send_rocketchat_notification(rc_message, e)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    asyncio.run(main())
