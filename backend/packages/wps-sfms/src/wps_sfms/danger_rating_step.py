"""Interpolate station danger ratings for one SFMS run."""

from wps_shared.db.models.sfms_run import SFMSRunLogJobName
from wps_shared.geospatial.geospatial import GDALResamplingMethod
from wps_shared.schemas.sfms import SFMSDaily
from wps_shared.sfms.raster_addresser import S3Key

from wps_sfms.interpolation.field import build_danger_rating_field
from wps_sfms.processors.danger_rating import DangerRatingInterpolator
from wps_sfms.run_context import SFMSRunContext


async def interpolate_danger_rating(
    context: SFMSRunContext, station_weather: list[SFMSDaily]
) -> S3Key:
    """Publish the station danger rating raster and record it in the run manifest."""
    mask_path = context.raster_addresser.get_mask_key()
    output_key = context.raster_addresser.get_danger_rating_key(
        context.datetime_to_process, context.run_type
    )
    processor = DangerRatingInterpolator(mask_path, build_danger_rating_field(station_weather))

    async def _interpolate() -> None:
        await processor.process(
            context.s3_client,
            context.base_fuel_raster_path,
            output_key,
            cog_resample_alg=GDALResamplingMethod.NEAREST_NEIGHBOUR,
        )

    await context.track(SFMSRunLogJobName.DANGER_RATING_INTERPOLATION, _interpolate)
    context.manifest.record_danger_rating_raster(output_key)
    return output_key
