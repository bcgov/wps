import asyncio
from datetime import datetime, timezone
import logging
import os
import sys
from wps_shared.db.crud.fire_watch import get_fire_watch_weather_by_model_run_parameter_id
from wps_shared.db.crud.weather_models import get_latest_prediction_timestamp_id_for_model
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.rocketchat_notifications import send_rocketchat_notification
from wps_shared.utils.time import get_utc_now
from wps_shared.wps_logging import configure_logging
from app.fire_watch.calculate_weather import FIREWATCH_WEATHER_MODEL, process_all_fire_watch_weather

logger = logging.getLogger(__name__)


async def main():
    if len(sys.argv) > 1:
        try:
            # command-line arg as 'YYYY-MM-DD'
            start_time = datetime.strptime(sys.argv[1], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            logger.error("Error: Please provide the date and hour in 'YYYY-MM-DD' format (as a single string)")
            sys.exit(1)
    else:
        # default to the current datetime
        start_time = get_utc_now()

    async with get_async_write_session_scope() as session:
        latest_prediction_id = await get_latest_prediction_timestamp_id_for_model(session, FIREWATCH_WEATHER_MODEL)

        fire_watch_weather_exists = await get_fire_watch_weather_by_model_run_parameter_id(session, latest_prediction_id)

        if fire_watch_weather_exists:
            logger.info(f"Fire watch weather already exists for the latest prediction - {latest_prediction_id}. Skipping processing.")
            return
    try:
        await process_all_fire_watch_weather(start_time)
    except Exception as e:
        logger.error("An exception occurred while processing fire watch weather data", exc_info=e)
        rc_message = ":scream: Encountered an error while processing fire watch weather data."
        send_rocketchat_notification(rc_message, e)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    asyncio.run(main())
