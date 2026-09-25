"""Code relating to processing HFI GeoTIFF files, and storing resultant data."""

import logging
import os
import tempfile
from datetime import date, datetime, timedelta
from time import perf_counter

import aiofiles
from wps_shared.db.crud.auto_spatial_advisory import (
    get_run_parameters_id,
    save_run_parameters,
)
from wps_shared.db.crud.snow import get_most_recent_processed_snow_by_date
from wps_shared.db.database import get_async_read_session_scope, get_async_write_session_scope
from wps_shared.db.models.snow import SnowSourceEnum
from wps_shared.geospatial.polygonize import polygonize_in_memory
from wps_shared.run_type import RunType
from wps_shared.utils.s3 import get_client

from app.auto_spatial_advisory.classify_hfi import classify_hfi
from app.auto_spatial_advisory.common import get_hfi_s3_key
from app.auto_spatial_advisory.hfi_filepath import (
    get_pmtiles_filename,
    get_pmtiles_filepath,
    get_raster_tif_filename,
    get_snow_masked_hfi_filepath,
)
from app.auto_spatial_advisory.snow import apply_snow_mask
from app.utils.pmtiles import tippecanoe_wrapper, write_geojson

logger = logging.getLogger(__name__)

HFI_GEOSPATIAL_PERMISSIONS = "public-read"
HFI_PMTILES_MIN_ZOOM = 4
HFI_PMTILES_MAX_ZOOM = 11


async def process_hfi(run_type: RunType, run_datetime: datetime, for_date: date):
    """Create a new hfi record for the given date.

    :param run_type: The type of run to process. (is it a forecast or actual run?)
    :param run_datetime: The date and time of the sfms run in UTC. (when was the hfi file created?)
    :param for_date: The date of the hfi to process. (when is the hfi for?)
    """

    # Skip if we already have this run
    async with get_async_read_session_scope() as session:
        existing_run = await get_run_parameters_id(session, run_type, run_datetime, for_date)
        if existing_run is not None:
            logger.info(
                "Skipping run, already processed for run_type:%s, run_datetime:%s, for_date:%s",
                run_type,
                run_datetime,
                for_date,
            )
            return
        last_processed_snow = await get_most_recent_processed_snow_by_date(
            session, run_datetime, SnowSourceEnum.viirs
        )

    logger.info(
        "Processing HFI %s for run date: %s, for date: %s", run_type, run_datetime, for_date
    )
    perf_start = perf_counter()

    hfi_key = get_hfi_s3_key(run_type, run_datetime, for_date)
    logger.info(f"Key to HFI in object storage: {hfi_key}")
    async with get_client() as (client, bucket):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_filename = os.path.join(temp_dir, "classified.tif")
            classify_hfi(hfi_key, temp_filename)
            # If something has gone wrong with the collection of snow coverage data and it has not
            # been collected within 7 days of the SFMS run datetime, don't apply an old snow mask,
            # work with the classified hfi data as is
            if (
                last_processed_snow is None
                or last_processed_snow[0].for_date + timedelta(days=7) < run_datetime
            ):
                logger.info(
                    "No recently processed snow data found. Proceeding with non-masked hfi data."
                )
                working_hfi_path = temp_filename
            else:
                # Create a snow coverage mask from previously downloaded snow data.
                working_hfi_path = apply_snow_mask(temp_filename, last_processed_snow[0], temp_dir)

            raster_filename = get_raster_tif_filename(for_date)
            raster_key = get_snow_masked_hfi_filepath(run_datetime, run_type, raster_filename)
            logger.info(f"Uploading file {raster_filename} to {raster_key}")
            async with aiofiles.open(working_hfi_path, "rb") as f:
                contents = await f.read()
            # HFI_GEOSPATIAL_PERMISSIONS: these need to be accessible to everyone
            await client.put_object(
                Bucket=bucket,
                Key=raster_key,
                ACL=HFI_GEOSPATIAL_PERMISSIONS,
                Body=contents,
            )
            logger.info("Done uploading %s", raster_key)
            with polygonize_in_memory(working_hfi_path, "hfi", "hfi") as layer:
                # We need a geojson file to pass to tippecanoe
                temp_geojson = write_geojson(layer, temp_dir)

                pmtiles_filename = get_pmtiles_filename(for_date)
                temp_pmtiles_filepath = os.path.join(temp_dir, pmtiles_filename)
                logger.info(f"Writing pmtiles -- {pmtiles_filename}")
                tippecanoe_wrapper(
                    temp_geojson,
                    temp_pmtiles_filepath,
                    min_zoom=HFI_PMTILES_MIN_ZOOM,
                    max_zoom=HFI_PMTILES_MAX_ZOOM,
                )

                key = get_pmtiles_filepath(run_datetime, run_type, pmtiles_filename)
                logger.info(f"Uploading file {pmtiles_filename} to {key}")

                async with aiofiles.open(temp_pmtiles_filepath, "rb") as f:
                    contents = await f.read()
                # HFI_GEOSPATIAL_PERMISSIONS: these need to be accessible to everyone
                await client.put_object(
                    Bucket=bucket,
                    Key=key,
                    ACL=HFI_GEOSPATIAL_PERMISSIONS,
                    Body=contents,
                )
                logger.info("Done uploading %s", key)

                async with get_async_write_session_scope() as session:
                    # Store the unique combination of run type, run datetime and for date in the
                    # run_parameters table
                    await save_run_parameters(session, run_type, run_datetime, for_date)

    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info("%f delta count before and after processing HFI", delta)
