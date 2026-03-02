"""
Job for running SFMS daily actuals weather interpolation and FWI processing.

Usage:
    python -m app.jobs.sfms_daily_actuals "YYYY-MM-DD"
    python -m app.jobs.sfms_daily_actuals  # Uses current date
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

from aiohttp import ClientSession

from wps_sfms.interpolation.source import (
    StationDCSource,
    StationDewPointSource,
    StationDMCSource,
    StationFFMCSource,
    StationPrecipitationSource,
    StationTemperatureSource,
    StationWindSpeedSource,
    StationWindVectorSource,
)
from wps_sfms.processors.fwi import DCCalculator, DMCCalculator, FFMCCalculator, FWIProcessor
from wps_sfms.processors.idw import Interpolator
from wps_sfms.processors.relative_humidity import RHInterpolator
from wps_sfms.processors.temperature import TemperatureInterpolator
from wps_sfms.processors.wind import WindDirectionInterpolator, WindSpeedInterpolator
from wps_shared.db.crud.fuel_layer import get_fuel_type_raster_by_year
from wps_shared.db.crud.sfms_run import save_sfms_run, track_sfms_run
from wps_shared.db.database import get_async_read_session_scope, get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum
from wps_shared.db.models.sfms_run import SFMSRunLogJobName
from wps_shared.sfms.raster_addresser import FWIParameter, SFMSInterpolatedWeatherParameter
from wps_shared.geospatial.wps_dataset import multi_wps_dataset_context
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser
from wps_shared.utils.s3_client import S3Client
from wps_shared.utils.time import get_utc_now
from wps_shared.wps_logging import configure_logging
from wps_wf1.wfwx_api import WfwxApi

logger = logging.getLogger(__name__)


def is_fwi_interpolation_day(dt: datetime) -> bool:
    """Return True if FWI indices should be re-interpolated from station observations.

    Re-interpolation resets the FWI grid from measured station values rather than
    calculating forward from yesterday's raster. This happens every Monday in
    April and May to align with the start of the fire season.
    """
    return dt.weekday() == 0 and dt.month in (4, 5)


async def run_weather_interpolation(
    datetime_to_process: datetime,
    raster_addresser: SFMSNGRasterAddresser,
    s3_client: S3Client,
    fuel_raster_path: str,
    sfms_actuals: list,
    sfms_run_id: int,
    session,
) -> None:
    """Interpolate weather rasters from station observations."""
    mask_path = raster_addresser.get_mask_key()
    dem_path = raster_addresser.get_dem_key()
    temp_key = raster_addresser.get_actual_weather_key(
        datetime_to_process, SFMSInterpolatedWeatherParameter.TEMP
    )
    temp_processor = TemperatureInterpolator(mask_path, dem_path)
    rh_processor = RHInterpolator(mask_path, dem_path, raster_addresser.gdal_path(temp_key))
    wind_speed_processor = WindSpeedInterpolator(mask_path)
    wind_direction_processor = WindDirectionInterpolator(mask_path)
    precip_processor = Interpolator(mask_path)

    @track_sfms_run(SFMSRunLogJobName.TEMPERATURE_INTERPOLATION, sfms_run_id, session)
    async def run_temperature_interpolation() -> None:
        temp_s3_key = await temp_processor.process(
            s3_client, fuel_raster_path, StationTemperatureSource(sfms_actuals), temp_key
        )
        logger.info("Temperature interpolation raster: %s", temp_s3_key)

    @track_sfms_run(SFMSRunLogJobName.RH_INTERPOLATION, sfms_run_id, session)
    async def run_rh_interpolation() -> None:
        rh_s3_key = await rh_processor.process(
            s3_client,
            fuel_raster_path,
            StationDewPointSource(sfms_actuals),
            raster_addresser.get_actual_weather_key(
                datetime_to_process, SFMSInterpolatedWeatherParameter.RH
            ),
        )
        logger.info("RH interpolation raster: %s", rh_s3_key)

    @track_sfms_run(SFMSRunLogJobName.PRECIPITATION_INTERPOLATION, sfms_run_id, session)
    async def run_precipitation_interpolation() -> None:
        precip_s3_key = await precip_processor.process(
            s3_client,
            fuel_raster_path,
            StationPrecipitationSource(sfms_actuals),
            raster_addresser.get_actual_weather_key(
                datetime_to_process, SFMSInterpolatedWeatherParameter.PRECIP
            ),
        )
        logger.info("Precip interpolation raster: %s", precip_s3_key)

    @track_sfms_run(SFMSRunLogJobName.WIND_SPEED_INTERPOLATION, sfms_run_id, session)
    async def run_wind_speed_interpolation() -> None:
        wind_speed_s3_key = await wind_speed_processor.process(
            s3_client,
            fuel_raster_path,
            StationWindSpeedSource(sfms_actuals),
            raster_addresser.get_actual_weather_key(
                datetime_to_process, SFMSInterpolatedWeatherParameter.WIND_SPEED
            ),
        )
        logger.info("Wind speed interpolation raster: %s", wind_speed_s3_key)

    @track_sfms_run(SFMSRunLogJobName.WIND_DIRECTION_INTERPOLATION, sfms_run_id, session)
    async def run_wind_direction_interpolation() -> None:
        wind_direction_s3_key = await wind_direction_processor.process(
            s3_client,
            fuel_raster_path,
            StationWindVectorSource(sfms_actuals),
            raster_addresser.get_actual_weather_key(
                datetime_to_process, SFMSInterpolatedWeatherParameter.WIND_DIRECTION
            ),
        )
        logger.info("Wind direction interpolation raster: %s", wind_direction_s3_key)

    await run_temperature_interpolation()
    await run_rh_interpolation()
    await run_wind_speed_interpolation()
    await run_wind_direction_interpolation()
    await run_precipitation_interpolation()


async def run_fwi_interpolation(
    datetime_to_process: datetime,
    raster_addresser: SFMSNGRasterAddresser,
    s3_client: S3Client,
    fuel_raster_path: str,
    sfms_actuals: list,
    sfms_run_id: int,
    session,
) -> None:
    """Re-interpolate FFMC, DMC, and DC from station observations."""
    logger.info(
        "Monday in %s — running FWI index interpolation", datetime_to_process.strftime("%B")
    )

    mask_path = raster_addresser.get_mask_key()
    fwi_sources = [
        (SFMSRunLogJobName.FFMC_INTERPOLATION, StationFFMCSource(sfms_actuals), FWIParameter.FFMC),
        (SFMSRunLogJobName.DMC_INTERPOLATION, StationDMCSource(sfms_actuals), FWIParameter.DMC),
        (SFMSRunLogJobName.DC_INTERPOLATION, StationDCSource(sfms_actuals), FWIParameter.DC),
    ]

    processor = Interpolator(mask_path)

    for job_name, source, fwi_param in fwi_sources:

        @track_sfms_run(job_name, sfms_run_id, session)
        async def _run(_source=source, _job_name=job_name, _fwi_param=fwi_param) -> None:
            output_key = raster_addresser.get_actual_index_key(datetime_to_process, _fwi_param)
            s3_key = await processor.process(s3_client, fuel_raster_path, _source, output_key)
            logger.info("%s interpolation raster: %s", _job_name.value, s3_key)

        await _run()


async def run_fwi_calculations(
    datetime_to_process: datetime,
    raster_addresser: SFMSNGRasterAddresser,
    s3_client: S3Client,
    sfms_run_id: int,
    session,
) -> None:
    """Calculate FFMC, DMC, and DC from interpolated weather and yesterday's actuals."""
    logger.info(
        "Calculating FWI from existing rasters for %s",
        datetime_to_process.date(),
    )

    fwi_processor = FWIProcessor(datetime_to_process)
    month = datetime_to_process.month

    fwi_calculations = [
        (SFMSRunLogJobName.FFMC_CALCULATION, FFMCCalculator()),
        (SFMSRunLogJobName.DMC_CALCULATION, DMCCalculator(month)),
        (SFMSRunLogJobName.DC_CALCULATION, DCCalculator(month)),
    ]

    for job_name, calculator in fwi_calculations:

        @track_sfms_run(job_name, sfms_run_id, session)
        async def _run(_calculator=calculator) -> None:
            _fwi_inputs = raster_addresser.get_actual_fwi_inputs(
                datetime_to_process, _calculator.fwi_param
            )
            await fwi_processor.calculate_index(
                s3_client, multi_wps_dataset_context, _calculator, _fwi_inputs
            )

        await _run()


async def run_sfms_daily_actuals(target_date: datetime) -> None:
    """Run SFMS daily weather interpolation and FWI updates for the given date."""
    logger.info("Starting SFMS daily actuals for %s", target_date.date())

    raster_addresser = SFMSNGRasterAddresser()

    # Create processor for target date (noon UTC hour 20)
    datetime_to_process = target_date.replace(hour=20, minute=0, second=0, microsecond=0)

    async with get_async_read_session_scope() as db_session:
        fuel_type_raster = await get_fuel_type_raster_by_year(db_session, datetime_to_process.year)
    if fuel_type_raster is None:
        raise RuntimeError(f"No fuel type raster found for {datetime_to_process.year}")
    fuel_raster_path = raster_addresser.gdal_path(fuel_type_raster.object_store_path)
    logger.info("Using reference raster: %s", fuel_raster_path)

    async with S3Client() as s3_client:
        # Fetch station observations from WF1
        async with ClientSession() as session:
            wfwx_api = WfwxApi(session)
            sfms_actuals = await wfwx_api.get_sfms_daily_actuals_all_stations(datetime_to_process)

        if not sfms_actuals:
            raise RuntimeError(f"No station observations found for {datetime_to_process}")

        async with get_async_write_session_scope() as session:
            station_codes = [actual.code for actual in sfms_actuals]
            sfms_run_id = await save_sfms_run(
                session,
                RunTypeEnum.actual,
                datetime_to_process.date(),
                get_utc_now(),
                station_codes,
            )

            await run_weather_interpolation(
                datetime_to_process,
                raster_addresser,
                s3_client,
                fuel_raster_path,
                sfms_actuals,
                sfms_run_id,
                session,
            )

            if is_fwi_interpolation_day(datetime_to_process):
                await run_fwi_interpolation(
                    datetime_to_process,
                    raster_addresser,
                    s3_client,
                    fuel_raster_path,
                    sfms_actuals,
                    sfms_run_id,
                    session,
                )
            else:
                await run_fwi_calculations(
                    datetime_to_process,
                    raster_addresser,
                    s3_client,
                    sfms_run_id,
                    session,
                )

    logger.info("SFMS daily actuals completed successfully for %s", target_date.date())


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
        loop.run_until_complete(run_sfms_daily_actuals(target_date))
    except Exception as exception:
        logger.error("An exception occurred while running SFMS daily actuals", exc_info=exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()
