"""The foliar moisture content step of an SFMS run."""

from wps_shared.db.models.sfms_run import SFMSRunLogJobName
from wps_shared.geospatial.wps_dataset import multi_wps_dataset_context
from wps_shared.sfms.raster_addresser import S3Key

from wps_sfms.processors.foliar_moisture_content import FoliarMoistureContentProcessor
from wps_sfms.run_context import SFMSRunContext


async def calculate_fmc(context: SFMSRunContext) -> S3Key:
    """
    Ensure the FMC raster for the run's date, from static rasters on the base fuel grid.

    :param context: The run's context
    :return: Key of the FMC raster
    """
    target_date = context.datetime_to_process.date()
    fmc_inputs = context.raster_addresser.get_fmc_inputs(
        [target_date], context.base_fuel_raster_path
    )
    context.manifest.record_fmc_static_inputs(fmc_inputs)
    # each forecast date reopens the static rasters; batch dates in one processor call
    # if FMC time matters
    await context.track(
        SFMSRunLogJobName.FOLIAR_MOISTURE_CONTENT,
        lambda: FoliarMoistureContentProcessor(context.raster_addresser).process(
            context.s3_client, multi_wps_dataset_context, fmc_inputs
        ),
    )
    context.manifest.record_fmc_raster(fmc_inputs, target_date)
    return fmc_inputs.output_keys[target_date]
