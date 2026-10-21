"""The primary fire behaviour prediction step of an SFMS run."""

import logging

from wps_shared.db.models.sfms_run import SFMSRunLogJobName
from wps_shared.geospatial.wps_dataset import multi_wps_dataset_context
from wps_shared.sfms.raster_addresser import (
    FWIParameter,
    GDALPath,
    S3Key,
    SFMSInterpolatedWeatherParameter,
)
from wps_shared.utils.s3_client import S3Client

from wps_sfms.processors.primary_fire_behaviour import PrimaryFireBehaviourProcessor
from wps_sfms.raster_inputs import PrimaryFireBehaviourInputs
from wps_sfms.run_context import FWIKeys, SFMSRunContext, WeatherKeys
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser

logger = logging.getLogger(__name__)


async def calculate_primary_fbp(
    context: SFMSRunContext,
    temporal_fuel_path: GDALPath,
    fmc_key: S3Key,
    weather_keys: WeatherKeys,
    fwi_keys: FWIKeys,
) -> None:
    """
    Calculate the same-day primary FBP products on the date's temporal fuel raster.

    :param context: The run's context
    :param temporal_fuel_path: The date's temporal fuel raster
    :param fmc_key: The run's FMC raster
    :param weather_keys: The run's weather rasters, of which it reads wind speed and direction
    :param fwi_keys: The run's index rasters, of which it reads FFMC and BUI
    """
    raster_addresser = context.raster_addresser
    slope_key = raster_addresser.get_slope_key()
    aspect_key = raster_addresser.get_aspect_key()
    context.manifest.record_static_rasters({"slope": slope_key, "aspect": aspect_key})

    async def _calculate() -> PrimaryFireBehaviourInputs:
        percent_conifer_path = await _resolve_percent_conifer_path(
            context.fuel_type_raster.year, raster_addresser, context.s3_client
        )
        context.manifest.record_percent_conifer_raster(percent_conifer_path)
        inputs = raster_addresser.get_primary_fire_behaviour_inputs(
            context.datetime_to_process,
            context.run_type,
            temporal_fuel_path,
            percent_conifer_path,
            raster_addresser.gdal_path(fwi_keys[FWIParameter.FFMC]),
            raster_addresser.gdal_path(fwi_keys[FWIParameter.BUI]),
            raster_addresser.gdal_path(weather_keys[SFMSInterpolatedWeatherParameter.WIND_SPEED]),
            raster_addresser.gdal_path(
                weather_keys[SFMSInterpolatedWeatherParameter.WIND_DIRECTION]
            ),
            raster_addresser.gdal_path(fmc_key),
            raster_addresser.gdal_path(slope_key),
            raster_addresser.gdal_path(aspect_key),
        )
        await PrimaryFireBehaviourProcessor(context.datetime_to_process).process(
            context.s3_client, multi_wps_dataset_context, inputs
        )
        return inputs

    inputs = await context.track(SFMSRunLogJobName.PRIMARY_FBP_CALCULATION, _calculate)
    for parameter, output_key in inputs.output_keys.items():
        context.manifest.record_raster_output(parameter, output_key)


async def _resolve_percent_conifer_path(
    fuel_raster_year: int,
    raster_addresser: SFMSNGRasterAddresser,
    s3_client: S3Client,
) -> GDALPath:
    """
    Resolve the percent-conifer raster matching the selected fuel-grid year.

    :param fuel_raster_year: Year of the run's base fuel grid
    :param raster_addresser: Addresser naming the raster's key
    :param s3_client: Client the raster is looked up with
    :return: Path of the percent-conifer raster
    """
    key = raster_addresser.get_percent_conifer_key(fuel_raster_year)
    if await s3_client.object_exists(key):
        logger.info("Using percent-conifer raster: %s", key)
        return raster_addresser.gdal_path(key)

    raise RuntimeError(
        f"No percent-conifer raster found for fuel-grid year {fuel_raster_year}: {key}"
    )
