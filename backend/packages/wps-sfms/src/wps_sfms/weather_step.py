"""The weather interpolation step of an SFMS run."""

import logging

from wps_shared.db.models.sfms_run import SFMSRunLogJobName
from wps_shared.schemas.sfms import SFMSDaily
from wps_shared.sfms.raster_addresser import (
    FWIParameter,
    S3Key,
    SFMSInterpolatedWeatherParameter,
)

from wps_sfms.interpolation.field import (
    build_dewpoint_field,
    build_precipitation_field,
    build_temperature_field,
    build_wind_speed_field,
    build_wind_vector_field,
)
from wps_sfms.processors.idw import Interpolator, RasterProcessor
from wps_sfms.processors.relative_humidity import RHInterpolator
from wps_sfms.processors.temperature import TemperatureInterpolator
from wps_sfms.processors.wind import WindDirectionInterpolator, WindSpeedInterpolator
from wps_sfms.run_context import SFMSRunContext, WeatherKeys

logger = logging.getLogger(__name__)


async def interpolate_raster(
    context: SFMSRunContext,
    job_name: SFMSRunLogJobName,
    parameter: SFMSInterpolatedWeatherParameter | FWIParameter,
    output_key: S3Key,
    processor: RasterProcessor,
) -> S3Key:
    """
    Interpolate one raster as a tracked job of the run.

    :param context: The run's context
    :param job_name: Job the interpolation is logged under
    :param parameter: Parameter the raster is recorded under in the manifest
    :param output_key: Key the raster is written to
    :param processor: Interpolator that writes the raster
    :return: Key of the interpolated raster
    """

    async def _interpolate() -> None:
        s3_key = await processor.process(
            context.s3_client, context.base_fuel_raster_path, output_key
        )
        logger.info("%s raster: %s", job_name.value, s3_key)

    await context.track(job_name, _interpolate)
    context.manifest.record_raster_output(parameter, output_key)
    return output_key


async def interpolate_weather(
    context: SFMSRunContext, station_weather: list[SFMSDaily]
) -> WeatherKeys:
    """
    Interpolate the run's weather rasters from its station weather.

    :param context: The run's context
    :param station_weather: The run's station weather
    :return: Keys of the temperature, RH, wind speed, wind direction and precipitation rasters
    """
    raster_addresser = context.raster_addresser
    mask_path = raster_addresser.get_mask_key()
    dem_path = raster_addresser.get_dem_key()
    context.manifest.record_static_rasters({"dem": dem_path, "mask": mask_path})

    def weather_key(param: SFMSInterpolatedWeatherParameter) -> S3Key:
        return raster_addresser.get_weather_key(
            context.datetime_to_process, param, context.run_type
        )

    temp_key = await interpolate_raster(
        context,
        SFMSRunLogJobName.TEMPERATURE_INTERPOLATION,
        SFMSInterpolatedWeatherParameter.TEMP,
        weather_key(SFMSInterpolatedWeatherParameter.TEMP),
        TemperatureInterpolator(mask_path, dem_path, build_temperature_field(station_weather)),
    )
    # RH is calculated from the dewpoint and the temperature just interpolated
    rh_key = await interpolate_raster(
        context,
        SFMSRunLogJobName.RH_INTERPOLATION,
        SFMSInterpolatedWeatherParameter.RH,
        weather_key(SFMSInterpolatedWeatherParameter.RH),
        RHInterpolator(
            mask_path,
            dem_path,
            raster_addresser.gdal_path(temp_key),
            build_dewpoint_field(station_weather),
        ),
    )
    wind_speed_key = await interpolate_raster(
        context,
        SFMSRunLogJobName.WIND_SPEED_INTERPOLATION,
        SFMSInterpolatedWeatherParameter.WIND_SPEED,
        weather_key(SFMSInterpolatedWeatherParameter.WIND_SPEED),
        WindSpeedInterpolator(mask_path, build_wind_speed_field(station_weather)),
    )
    wind_direction_key = await interpolate_raster(
        context,
        SFMSRunLogJobName.WIND_DIRECTION_INTERPOLATION,
        SFMSInterpolatedWeatherParameter.WIND_DIRECTION,
        weather_key(SFMSInterpolatedWeatherParameter.WIND_DIRECTION),
        WindDirectionInterpolator(mask_path, build_wind_vector_field(station_weather)),
    )
    precip_key = await interpolate_raster(
        context,
        SFMSRunLogJobName.PRECIPITATION_INTERPOLATION,
        SFMSInterpolatedWeatherParameter.PRECIP,
        weather_key(SFMSInterpolatedWeatherParameter.PRECIP),
        Interpolator(mask_path, build_precipitation_field(station_weather)),
    )
    return {
        SFMSInterpolatedWeatherParameter.TEMP: temp_key,
        SFMSInterpolatedWeatherParameter.RH: rh_key,
        SFMSInterpolatedWeatherParameter.WIND_SPEED: wind_speed_key,
        SFMSInterpolatedWeatherParameter.WIND_DIRECTION: wind_direction_key,
        SFMSInterpolatedWeatherParameter.PRECIP: precip_key,
    }
