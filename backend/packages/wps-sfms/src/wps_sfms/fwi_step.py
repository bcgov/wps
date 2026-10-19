"""The FWI steps of an SFMS run: calculating forward from previous-day seeds, or re-interpolating
from station weather on April and May Mondays."""

import logging
from datetime import datetime, timedelta

from wps_shared.db.models.sfms_run import SFMSRunLogJobName
from wps_shared.geospatial.wps_dataset import multi_wps_dataset_context
from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import FWIParameter, S3Key
from wps_shared.utils.s3_client import S3Client

from wps_sfms.interpolation.field import build_dc_field, build_dmc_field, build_ffmc_field
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
from wps_sfms.processors.idw import Interpolator
from wps_sfms.raster_inputs import FWIInputs
from wps_sfms.run_context import FWIKeys, SFMSRunContext, WeatherKeys
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser
from wps_sfms.weather_step import interpolate_raster

logger = logging.getLogger(__name__)

FWI_CALCULATION_JOB_NAMES = {
    FWIParameter.FFMC: SFMSRunLogJobName.FFMC_CALCULATION,
    FWIParameter.DMC: SFMSRunLogJobName.DMC_CALCULATION,
    FWIParameter.DC: SFMSRunLogJobName.DC_CALCULATION,
    FWIParameter.ISI: SFMSRunLogJobName.ISI_CALCULATION,
    FWIParameter.BUI: SFMSRunLogJobName.BUI_CALCULATION,
    FWIParameter.FWI: SFMSRunLogJobName.FWI_CALCULATION,
}


async def calculate_fwi_index(
    context: SFMSRunContext,
    calculator: FWICalculator,
    weather_keys: WeatherKeys,
    index_keys: FWIKeys,
) -> S3Key:
    """
    Calculate one FWI index for the run's date as a tracked job.

    :param context: The run's context
    :param calculator: Calculator for the index
    :param weather_keys: The run's same-day weather rasters
    :param index_keys: The index rasters it reads: the previous day's value for FFMC, DMC and DC,
        the same day's FFMC for ISI, DMC and DC for BUI, and ISI and BUI for FWI
    :return: Key of the index raster
    """
    fwi_param = calculator.fwi_param

    async def _calculate() -> FWIInputs:
        inputs = context.raster_addresser.get_fwi_inputs(
            context.datetime_to_process, fwi_param, context.run_type, weather_keys, index_keys
        )
        await FWIProcessor(context.datetime_to_process).calculate_index(
            context.s3_client, multi_wps_dataset_context, calculator, inputs
        )
        return inputs

    inputs = await context.track(FWI_CALCULATION_JOB_NAMES[fwi_param], _calculate)
    context.manifest.record_raster_output(fwi_param, inputs.output_key)
    return inputs.output_key


def seed_run_type(context: SFMSRunContext) -> RunType:
    """
    The run type of the previous-day rasters the run calculates FWI forward from.

    The run seeds from the actual rasters when the previous day is its ``seed_actual_date``, and
    from the previous day's forecast otherwise: an actual run and the first forecast date seed
    from actuals, later forecast dates from the forecast before them.

    :param context: The run's context
    :return: Run type of the seed rasters
    """
    previous_date = (context.datetime_to_process - timedelta(days=1)).date()
    if previous_date == context.seed_actual_date:
        return RunType.ACTUAL
    return RunType.FORECAST


def seed_keys(
    datetime_to_process: datetime,
    raster_addresser: SFMSNGRasterAddresser,
    seed_run_type: RunType,
) -> FWIKeys:
    """
    The previous-day FFMC, DMC and DC raster keys of the seed run type.

    :param datetime_to_process: UTC datetime being processed
    :param raster_addresser: Addresser naming the seed keys
    :param seed_run_type: Run type of the seed rasters
    :return: Keys of the previous-day FFMC, DMC and DC rasters
    """
    previous_date = datetime_to_process - timedelta(days=1)
    return {
        param: raster_addresser.get_index_key(previous_date, param, seed_run_type)
        for param in (FWIParameter.FFMC, FWIParameter.DMC, FWIParameter.DC)
    }


async def missing_seed_keys(
    datetime_to_process: datetime,
    raster_addresser: SFMSNGRasterAddresser,
    s3_client: S3Client,
    seed_run_type: RunType,
) -> list[str]:
    """
    Any previous-day FFMC, DMC and DC rasters of the seed run type that don't exist.

    :param datetime_to_process: UTC datetime being processed
    :param raster_addresser: Addresser naming the seed keys
    :param s3_client: Client the seeds are looked up with
    :param seed_run_type: Run type of the seed rasters
    :return: ``param=key`` for each missing seed, empty when all exist
    """
    missing_keys = []
    for param, key in seed_keys(datetime_to_process, raster_addresser, seed_run_type).items():
        if not await s3_client.all_objects_exist(key):
            missing_keys.append(f"{param.value}={key}")
    return missing_keys


async def calculate_fwi(context: SFMSRunContext, weather_keys: WeatherKeys) -> FWIKeys | None:
    """
    Calculate the full FWI chain forward from the previous day's FFMC, DMC and DC.

    Missing seeds are recorded as a failure, and FWI is skipped: a run can legitimately start
    without seeds (season start, backfills) and still produces weather.

    :param context: The run's context
    :param weather_keys: The run's same-day weather rasters
    :return: Keys of the six index rasters, or None when seeds are missing
    """
    run_seed_type = seed_run_type(context)
    missing_previous_keys = await missing_seed_keys(
        context.datetime_to_process, context.raster_addresser, context.s3_client, run_seed_type
    )
    if missing_previous_keys:
        previous_date = context.datetime_to_process - timedelta(days=1)
        message = (
            f"Missing previous-day {run_seed_type.value} index rasters for "
            f"{previous_date.date()}: {', '.join(missing_previous_keys)}"
        )
        # recorded so a run without FWI or FBP isn't reported as a success
        context.manifest.record_failure("fwi_seed_check", RuntimeError(message))
        logger.warning(
            "Skipping FWI calculations for %s because %s",
            context.datetime_to_process.date(),
            message,
        )
        return None

    seeds = seed_keys(context.datetime_to_process, context.raster_addresser, run_seed_type)
    context.manifest.record_seed_rasters(seeds)
    logger.info(
        "Calculating %s FWI from existing rasters for %s",
        context.run_type.value,
        context.datetime_to_process.date(),
    )
    month = context.datetime_to_process.month
    # FFMC, DMC and DC each calculate forward from their own previous-day value
    ffmc_key = await calculate_fwi_index(
        context, FFMCCalculator(), weather_keys, {FWIParameter.FFMC: seeds[FWIParameter.FFMC]}
    )
    dmc_key = await calculate_fwi_index(
        context, DMCCalculator(month), weather_keys, {FWIParameter.DMC: seeds[FWIParameter.DMC]}
    )
    dc_key = await calculate_fwi_index(
        context, DCCalculator(month), weather_keys, {FWIParameter.DC: seeds[FWIParameter.DC]}
    )
    isi_key = await calculate_fwi_index(
        context, ISICalculator(), weather_keys, {FWIParameter.FFMC: ffmc_key}
    )
    bui_key = await calculate_fwi_index(
        context, BUICalculator(), weather_keys, {FWIParameter.DMC: dmc_key, FWIParameter.DC: dc_key}
    )
    fwi_key = await calculate_fwi_index(
        context,
        FWIFinalCalculator(),
        weather_keys,
        {FWIParameter.ISI: isi_key, FWIParameter.BUI: bui_key},
    )
    return {
        FWIParameter.FFMC: ffmc_key,
        FWIParameter.DMC: dmc_key,
        FWIParameter.DC: dc_key,
        FWIParameter.ISI: isi_key,
        FWIParameter.BUI: bui_key,
        FWIParameter.FWI: fwi_key,
    }


async def interpolate_fwi(
    context: SFMSRunContext, station_weather: list, weather_keys: WeatherKeys
) -> FWIKeys:
    """
    Reset FFMC, DMC and DC from station weather, then derive ISI, BUI and FWI from them.

    Runs on April and May Mondays in place of calculating forward from previous-day seeds.

    :param context: The run's context
    :param station_weather: The run's station weather
    :param weather_keys: The run's same-day weather rasters
    :return: Keys of the six index rasters
    """
    logger.info(
        "Monday in %s - running FWI index interpolation",
        context.datetime_to_process.strftime("%B"),
    )
    mask_path = context.raster_addresser.get_mask_key()
    context.manifest.record_static_rasters({"mask": mask_path})

    def index_key(param: FWIParameter) -> S3Key:
        return context.raster_addresser.get_index_key(
            context.datetime_to_process, param, context.run_type
        )

    ffmc_key = await interpolate_raster(
        context,
        SFMSRunLogJobName.FFMC_INTERPOLATION,
        FWIParameter.FFMC,
        index_key(FWIParameter.FFMC),
        Interpolator(mask_path, build_ffmc_field(station_weather)),
    )
    dmc_key = await interpolate_raster(
        context,
        SFMSRunLogJobName.DMC_INTERPOLATION,
        FWIParameter.DMC,
        index_key(FWIParameter.DMC),
        Interpolator(mask_path, build_dmc_field(station_weather)),
    )
    dc_key = await interpolate_raster(
        context,
        SFMSRunLogJobName.DC_INTERPOLATION,
        FWIParameter.DC,
        index_key(FWIParameter.DC),
        Interpolator(mask_path, build_dc_field(station_weather)),
    )
    isi_key = await calculate_fwi_index(
        context, ISICalculator(), weather_keys, {FWIParameter.FFMC: ffmc_key}
    )
    bui_key = await calculate_fwi_index(
        context, BUICalculator(), weather_keys, {FWIParameter.DMC: dmc_key, FWIParameter.DC: dc_key}
    )
    fwi_key = await calculate_fwi_index(
        context,
        FWIFinalCalculator(),
        weather_keys,
        {FWIParameter.ISI: isi_key, FWIParameter.BUI: bui_key},
    )
    return {
        FWIParameter.FFMC: ffmc_key,
        FWIParameter.DMC: dmc_key,
        FWIParameter.DC: dc_key,
        FWIParameter.ISI: isi_key,
        FWIParameter.BUI: bui_key,
        FWIParameter.FWI: fwi_key,
    }
