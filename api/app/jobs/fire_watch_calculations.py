import asyncio
from datetime import datetime, timezone
import logging
from wps_shared.db.crud.fire_watch import get_fire_watch_weather_by_model_run_parameter_id
from wps_shared.db.crud.weather_models import get_latest_prediction_timestamp_id_for_model
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.utils.time import get_utc_now
from wps_shared.wps_logging import configure_logging
from app.fire_watch.calculate_weather import FIREWATCH_WEATHER_MODEL, process_all_fire_watch_weather

logger = logging.getLogger(__name__)


async def main():
    start_date = get_utc_now()

    async with get_async_write_session_scope() as session:
        latest_prediction_id = await get_latest_prediction_timestamp_id_for_model(session, FIREWATCH_WEATHER_MODEL)

        fire_watch_weather_exists = await get_fire_watch_weather_by_model_run_parameter_id(session, latest_prediction_id)

        if fire_watch_weather_exists:
            logger.info(f"Fire watch weather already exists for the latest prediction - {latest_prediction_id}. Skipping processing.")
            return

    await process_all_fire_watch_weather(start_date)


if __name__ == "__main__":
    configure_logging()
    asyncio.run(main())
