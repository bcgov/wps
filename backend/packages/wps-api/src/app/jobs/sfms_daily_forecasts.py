"""
Job for running SFMS daily forecast weather interpolation and FWI processing.

Usage:
    python -m app.jobs.sfms_daily_forecasts "YYYY-MM-DD"
    python -m app.jobs.sfms_daily_forecasts  # Uses current date
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

from aiohttp import ClientSession
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser
from wps_shared.chatops_notification import send_chatops_notification
from wps_shared.db.crud.fuel_layer import get_fuel_type_raster_by_year
from wps_shared.db.crud.sfms_run import save_sfms_run
from wps_shared.db.database import get_async_read_session_scope, get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum
from wps_shared.run_type import RunType
from wps_shared.utils.s3_client import S3Client
from wps_shared.utils.time import get_utc_now
from wps_shared.wps_logging import configure_logging
from wps_wf1.wfwx_api import WfwxApi

from app.jobs.sfms_run_pipeline import run_fwi_calculations, run_weather_interpolation

logger = logging.getLogger(__name__)

FORECAST_DAYS = 3


def forecast_datetimes(target_date: datetime) -> list[datetime]:
    """Return the next three forecast dates normalized to 20:00 UTC."""
    base_datetime = target_date.replace(hour=20, minute=0, second=0, microsecond=0)
    return [base_datetime + timedelta(days=day) for day in range(1, FORECAST_DAYS + 1)]


async def run_sfms_daily_forecasts(target_date: datetime) -> None:
    """Run SFMS forecast weather interpolation and FWI updates for the next three days."""
    logger.info("Starting SFMS daily forecasts from %s", target_date.date())

    raster_addresser = SFMSNGRasterAddresser()
    datetimes_to_process = forecast_datetimes(target_date)

    async with S3Client() as s3_client:
        async with ClientSession() as client_session:
            wfwx_api = WfwxApi(client_session)

            async with get_async_read_session_scope() as read_session:
                # all the forecasts will use the same fuel raster (only 1 year needed)
                fuel_raster_year = datetimes_to_process[0].year
                fuel_type_raster = await get_fuel_type_raster_by_year(
                    read_session, fuel_raster_year
                )
                if fuel_type_raster is None:
                    raise RuntimeError(f"No fuel type raster found for {fuel_raster_year}")
                fuel_raster_path = raster_addresser.gdal_path(fuel_type_raster.object_store_path)
                logger.info("Using reference raster: %s", fuel_raster_path)

                async with get_async_write_session_scope() as write_session:
                    for index, datetime_to_process in enumerate(datetimes_to_process):
                        sfms_forecasts = await wfwx_api.get_sfms_daily_forecasts_all_stations(
                            datetime_to_process
                        )
                        if not sfms_forecasts:
                            raise RuntimeError(
                                f"No station forecasts found for {datetime_to_process}"
                            )

                        station_codes = [forecast.code for forecast in sfms_forecasts]
                        sfms_run_id = await save_sfms_run(
                            write_session,
                            RunTypeEnum.forecast,
                            datetime_to_process.date(),
                            get_utc_now(),
                            station_codes,
                        )

                        await run_weather_interpolation(
                            datetime_to_process,
                            raster_addresser,
                            s3_client,
                            fuel_raster_path,
                            sfms_forecasts,
                            sfms_run_id,
                            write_session,
                            RunType.FORECAST,
                        )

                        previous_base_run_type = RunType.ACTUAL if index == 0 else RunType.FORECAST
                        await run_fwi_calculations(
                            datetime_to_process,
                            raster_addresser,
                            s3_client,
                            sfms_run_id,
                            write_session,
                            RunType.FORECAST,
                            previous_base_run_type=previous_base_run_type,
                            raise_on_missing_seed_keys=True,
                        )

    logger.info("SFMS daily forecasts completed successfully from %s", target_date.date())


def main():
    """Main entry point for the job."""
    if len(sys.argv) > 1:
        try:
            target_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            logger.error("Error: Please provide the date in 'YYYY-MM-DD' format")
            sys.exit(1)
    else:
        target_date = get_utc_now()

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_sfms_daily_forecasts(target_date))
    except Exception as exception:
        logger.exception("An exception occurred while running SFMS daily forecasts")
        chatops_message = "Encountered error running SFMS daily forecasts"
        send_chatops_notification(chatops_message, exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()
