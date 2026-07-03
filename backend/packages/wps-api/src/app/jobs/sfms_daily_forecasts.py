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
from datetime import date, datetime, timedelta, timezone

from aiohttp import ClientSession
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser
from wps_shared.chatops_notification import send_chatops_notification
from wps_shared.db.crud.fuel_layer import get_fuel_type_raster_by_year
from wps_shared.db.crud.sfms_run import save_sfms_run
from wps_shared.db.database import get_async_read_session_scope, get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum
from wps_shared.run_type import RunType
from wps_shared.utils.s3_client import S3Client
from wps_shared.utils.time import (
    assert_all_utc,
    get_utc_now,
    vancouver_tz,
)
from wps_shared.wps_logging import configure_logging
from wps_wf1.wfwx_api import WfwxApi

from app.jobs.sfms_run_pipeline import (
    _missing_seed_keys,
    run_fwi_calculations,
    run_weather_interpolation,
)

logger = logging.getLogger(__name__)

FORECAST_DAYS = 3
ACTUALS_AVAILABLE_HOUR_PDT = 15


def forecast_datetimes(seed_actual_date: date) -> list[datetime]:
    """Return the next three forecast dates normalized to 20:00 UTC."""
    base_datetime = datetime(
        seed_actual_date.year,
        seed_actual_date.month,
        seed_actual_date.day,
        hour=20,
        tzinfo=timezone.utc,
    )
    return [base_datetime + timedelta(days=day) for day in range(1, FORECAST_DAYS + 1)]


def expected_actual_target_date(run_datetime: datetime) -> date:
    """Return the actual target date this forecast run is expected to seed from."""
    assert_all_utc(run_datetime)
    run_datetime_local = run_datetime.astimezone(vancouver_tz)
    target_date = run_datetime_local.date()
    if run_datetime_local.hour < ACTUALS_AVAILABLE_HOUR_PDT:
        return target_date - timedelta(days=1)
    return target_date


def run_datetime_for_cli_date(run_date: date, current_datetime: datetime) -> datetime:
    """Return a UTC run datetime for the CLI date at the current local time."""
    assert_all_utc(current_datetime)
    current_datetime_local = current_datetime.astimezone(vancouver_tz)
    cli_datetime = datetime(
        run_date.year,
        run_date.month,
        run_date.day,
        current_datetime_local.hour,
        current_datetime_local.minute,
        current_datetime_local.second,
        tzinfo=vancouver_tz,
    )
    return cli_datetime.astimezone(timezone.utc)


async def run_sfms_daily_forecasts(run_datetime: datetime) -> None:
    """Run SFMS forecast weather interpolation and FWI updates for the next three days."""
    assert_all_utc(run_datetime)
    logger.info("Starting SFMS daily forecasts from %s", run_datetime.date())

    raster_addresser = SFMSNGRasterAddresser()
    seed_actual_date = expected_actual_target_date(run_datetime)
    logger.info("Using %s actual rasters as forecast seed", seed_actual_date)
    datetimes_to_process = forecast_datetimes(seed_actual_date)

    async with S3Client() as s3_client:
        missing_actual_seed_keys = await _missing_seed_keys(
            datetimes_to_process[0],
            raster_addresser,
            s3_client,
            RunType.ACTUAL,
        )
        if missing_actual_seed_keys:
            raise RuntimeError(
                f"Missing actual seed rasters for {seed_actual_date}: "
                f"{', '.join(missing_actual_seed_keys)}"
            )

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

    logger.info("SFMS daily forecasts completed successfully from %s", run_datetime.date())


def main():
    """Main entry point for the job."""
    if len(sys.argv) > 1:
        try:
            run_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
            target_date = run_datetime_for_cli_date(run_date, get_utc_now())
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
