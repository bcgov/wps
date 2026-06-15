"""Shared SFMS weather interpolation and FWI calculation pipeline."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Awaitable, Callable

from wps_sfms.interpolation.field import (
    build_dc_field,
    build_dewpoint_field,
    build_dmc_field,
    build_ffmc_field,
    build_precipitation_field,
    build_temperature_field,
    build_wind_speed_field,
    build_wind_vector_field,
)
from wps_sfms.processors.fwi import (
    BUICalculator,
    DCCalculator,
    DMCCalculator,
    FFMCCalculator,
    FWICalculator,
    FWIFinalCalculator,
    FWIProcessor,
    ISICalculator,
)
from wps_sfms.processors.idw import Interpolator, RasterProcessor
from wps_sfms.processors.relative_humidity import RHInterpolator
from wps_sfms.processors.temperature import TemperatureInterpolator
from wps_sfms.processors.wind import WindDirectionInterpolator, WindSpeedInterpolator
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser
from wps_shared.db.crud.sfms_run import track_sfms_run
from wps_shared.db.models.sfms_run import SFMSRunLogJobName
from wps_shared.geospatial.wps_dataset import multi_wps_dataset_context
from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import FWIParameter, SFMSInterpolatedWeatherParameter
from wps_shared.utils.s3_client import S3Client

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RasterInterpolationJob:
    job_name: SFMSRunLogJobName
    output_key: str
    log_label: str
    processor: RasterProcessor


@dataclass(frozen=True)
class FWICalculationJob:
    job_name: SFMSRunLogJobName
    calculator: FWICalculator


async def _run_tracked_job(
    job_name: SFMSRunLogJobName,
    sfms_run_id: int,
    session,
    action: Callable[[], Awaitable[object]],
):
    @track_sfms_run(job_name, sfms_run_id, session)
    async def _wrapped():
        return await action()

    return await _wrapped()


async def _process_raster_job(
    *,
    job_name: SFMSRunLogJobName,
    sfms_run_id: int,
    session,
    processor: RasterProcessor,
    s3_client: S3Client,
    fuel_raster_path: str,
    output_key: str,
    log_label: str,
) -> None:
    async def _run() -> None:
        s3_key = await processor.process(s3_client, fuel_raster_path, output_key)
        logger.info("%s: %s", log_label, s3_key)

    await _run_tracked_job(job_name, sfms_run_id, session, _run)


async def _missing_seed_keys(
    datetime_to_process: datetime,
    raster_addresser: SFMSNGRasterAddresser,
    s3_client: S3Client,
    run_type: RunType = RunType.ACTUAL,
) -> list[str]:
    """Return any missing previous-day FFMC/DMC/DC seed rasters."""
    previous_date = datetime_to_process - timedelta(days=1)
    missing_keys = []
    for param in (FWIParameter.FFMC, FWIParameter.DMC, FWIParameter.DC):
        key = raster_addresser.get_index_key(previous_date, param, run_type)
        if not await s3_client.all_objects_exist(key):
            missing_keys.append(f"{param.value}={key}")

    return missing_keys


async def run_weather_interpolation(
    datetime_to_process: datetime,
    raster_addresser: SFMSNGRasterAddresser,
    s3_client: S3Client,
    fuel_raster_path: str,
    station_weather: list,
    sfms_run_id: int,
    session,
    run_type: RunType,
) -> None:
    """Interpolate weather rasters from station weather records."""
    mask_path = raster_addresser.get_mask_key()
    dem_path = raster_addresser.get_dem_key()
    temp_output_key = raster_addresser.get_weather_key(
        datetime_to_process, SFMSInterpolatedWeatherParameter.TEMP, run_type
    )
    temp_raster_path = raster_addresser.gdal_path(temp_output_key)
    jobs = [
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.TEMPERATURE_INTERPOLATION,
            output_key=temp_output_key,
            log_label="Temperature interpolation raster",
            processor=TemperatureInterpolator(
                mask_path, dem_path, build_temperature_field(station_weather)
            ),
        ),
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.RH_INTERPOLATION,
            output_key=raster_addresser.get_weather_key(
                datetime_to_process, SFMSInterpolatedWeatherParameter.RH, run_type
            ),
            log_label="RH interpolation raster",
            processor=RHInterpolator(
                mask_path, dem_path, temp_raster_path, build_dewpoint_field(station_weather)
            ),
        ),
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.WIND_SPEED_INTERPOLATION,
            output_key=raster_addresser.get_weather_key(
                datetime_to_process, SFMSInterpolatedWeatherParameter.WIND_SPEED, run_type
            ),
            log_label="Wind speed interpolation raster",
            processor=WindSpeedInterpolator(mask_path, build_wind_speed_field(station_weather)),
        ),
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.WIND_DIRECTION_INTERPOLATION,
            output_key=raster_addresser.get_weather_key(
                datetime_to_process, SFMSInterpolatedWeatherParameter.WIND_DIRECTION, run_type
            ),
            log_label="Wind direction interpolation raster",
            processor=WindDirectionInterpolator(
                mask_path, build_wind_vector_field(station_weather)
            ),
        ),
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.PRECIPITATION_INTERPOLATION,
            output_key=raster_addresser.get_weather_key(
                datetime_to_process, SFMSInterpolatedWeatherParameter.PRECIP, run_type
            ),
            log_label="Precip interpolation raster",
            processor=Interpolator(mask_path, build_precipitation_field(station_weather)),
        ),
    ]

    for job in jobs:
        await _process_raster_job(
            job_name=job.job_name,
            sfms_run_id=sfms_run_id,
            session=session,
            processor=job.processor,
            s3_client=s3_client,
            fuel_raster_path=fuel_raster_path,
            output_key=job.output_key,
            log_label=job.log_label,
        )


async def run_fwi_interpolation(
    datetime_to_process: datetime,
    raster_addresser: SFMSNGRasterAddresser,
    s3_client: S3Client,
    fuel_raster_path: str,
    station_weather: list,
    sfms_run_id: int,
    session,
    run_type: RunType,
) -> None:
    """Re-interpolate FFMC, DMC, and DC from station weather records."""
    logger.info(
        "Monday in %s - running FWI index interpolation", datetime_to_process.strftime("%B")
    )

    mask_path = raster_addresser.get_mask_key()
    jobs = [
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.FFMC_INTERPOLATION,
            output_key=raster_addresser.get_index_key(
                datetime_to_process, FWIParameter.FFMC, run_type
            ),
            log_label=f"{SFMSRunLogJobName.FFMC_INTERPOLATION.value} raster",
            processor=Interpolator(mask_path, build_ffmc_field(station_weather)),
        ),
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.DMC_INTERPOLATION,
            output_key=raster_addresser.get_index_key(
                datetime_to_process, FWIParameter.DMC, run_type
            ),
            log_label=f"{SFMSRunLogJobName.DMC_INTERPOLATION.value} raster",
            processor=Interpolator(mask_path, build_dmc_field(station_weather)),
        ),
        RasterInterpolationJob(
            job_name=SFMSRunLogJobName.DC_INTERPOLATION,
            output_key=raster_addresser.get_index_key(
                datetime_to_process, FWIParameter.DC, run_type
            ),
            log_label=f"{SFMSRunLogJobName.DC_INTERPOLATION.value} raster",
            processor=Interpolator(mask_path, build_dc_field(station_weather)),
        ),
    ]

    for job in jobs:
        await _process_raster_job(
            job_name=job.job_name,
            sfms_run_id=sfms_run_id,
            session=session,
            processor=job.processor,
            s3_client=s3_client,
            fuel_raster_path=fuel_raster_path,
            output_key=job.output_key,
            log_label=job.log_label,
        )


async def _run_fwi_calculation_jobs(
    datetime_to_process: datetime,
    raster_addresser: SFMSNGRasterAddresser,
    s3_client: S3Client,
    sfms_run_id: int,
    session,
    calculators: tuple[FWICalculator, ...],
    run_type: RunType,
    previous_base_run_type: RunType | None = None,
) -> None:
    """Run the provided FWI calculator jobs in order."""
    logger.info(
        "Calculating %s FWI from existing rasters for %s",
        run_type.value,
        datetime_to_process.date(),
    )

    fwi_processor = FWIProcessor(datetime_to_process)

    job_names_by_param = {
        FWIParameter.FFMC: SFMSRunLogJobName.FFMC_CALCULATION,
        FWIParameter.DMC: SFMSRunLogJobName.DMC_CALCULATION,
        FWIParameter.DC: SFMSRunLogJobName.DC_CALCULATION,
        FWIParameter.ISI: SFMSRunLogJobName.ISI_CALCULATION,
        FWIParameter.BUI: SFMSRunLogJobName.BUI_CALCULATION,
        FWIParameter.FWI: SFMSRunLogJobName.FWI_CALCULATION,
    }
    jobs = [
        FWICalculationJob(
            job_name=job_names_by_param[calculator.fwi_param],
            calculator=calculator,
        )
        for calculator in calculators
    ]

    for job in jobs:

        async def _run(_calculator=job.calculator) -> None:
            _fwi_inputs = raster_addresser.get_fwi_inputs(
                datetime_to_process,
                _calculator.fwi_param,
                run_type,
                previous_base_run_type=previous_base_run_type,
            )
            await fwi_processor.calculate_index(
                s3_client, multi_wps_dataset_context, _calculator, _fwi_inputs
            )

        await _run_tracked_job(job.job_name, sfms_run_id, session, _run)


async def run_fwi_calculations(
    datetime_to_process: datetime,
    raster_addresser: SFMSNGRasterAddresser,
    s3_client: S3Client,
    sfms_run_id: int,
    session,
    run_type: RunType,
    previous_base_run_type: RunType | None = None,
    raise_on_missing_seed_keys: bool = False,
) -> None:
    """Calculate the full FWI chain from weather and previous-day seeds."""
    month = datetime_to_process.month
    seed_run_type = previous_base_run_type or run_type
    missing_previous_keys = await _missing_seed_keys(
        datetime_to_process,
        raster_addresser,
        s3_client,
        seed_run_type,
    )
    if missing_previous_keys:
        previous_date = datetime_to_process - timedelta(days=1)
        message = (
            f"Missing previous-day {seed_run_type.value} index rasters for "
            f"{previous_date.date()}: {', '.join(missing_previous_keys)}"
        )
        if raise_on_missing_seed_keys:
            raise RuntimeError(message)
        logger.warning(
            "Skipping FWI calculations for %s because %s",
            datetime_to_process.date(),
            message,
        )
        return

    await _run_fwi_calculation_jobs(
        datetime_to_process,
        raster_addresser,
        s3_client,
        sfms_run_id,
        session,
        (
            FFMCCalculator(),
            DMCCalculator(month),
            DCCalculator(month),
            ISICalculator(),
            BUICalculator(),
            FWIFinalCalculator(),
        ),
        run_type,
        previous_base_run_type=previous_base_run_type,
    )


async def run_derived_fwi_calculations(
    datetime_to_process: datetime,
    raster_addresser: SFMSNGRasterAddresser,
    s3_client: S3Client,
    sfms_run_id: int,
    session,
    run_type: RunType,
) -> None:
    """Calculate ISI, BUI, and FWI from same-day weather and interpolated base indices."""
    await _run_fwi_calculation_jobs(
        datetime_to_process,
        raster_addresser,
        s3_client,
        sfms_run_id,
        session,
        (ISICalculator(), BUICalculator(), FWIFinalCalculator()),
        run_type,
    )
