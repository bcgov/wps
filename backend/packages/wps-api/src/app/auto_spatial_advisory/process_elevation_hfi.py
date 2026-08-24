"""Takes a classified HFI image and calculates TPI-based elevation statistics associated with advisory areas per fire zone."""

import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from time import perf_counter
from typing import Dict

import numpy as np
from osgeo import gdal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import text
from wps_shared import config
from wps_shared.db.crud.auto_spatial_advisory import (
    get_run_parameters_id,
    save_advisory_elevation_tpi_stats,
)
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import AdvisoryTPIStats
from wps_shared.geospatial.geospatial import raster_mul, warp_to_match_raster
from wps_shared.run_type import RunType

from app.auto_spatial_advisory.hfi_filepath import (
    get_raster_tif_filename,
    get_snow_masked_hfi_filepath,
)
from app.auto_spatial_advisory.process_fuel_type_area import get_advisory_shape

logger = logging.getLogger(__name__)


async def process_hfi_elevation(run_type: RunType, run_datetime: datetime, for_date: date):
    """Create new elevation based hfi analysis records for the given date.

    :param run_type: The type of run to process. (is it a forecast or actual run?)
    :param run_datetime: The date and time of the sfms run in UTC. (when was the hfi file created?)
    :param for_date: The date of the hfi to process. (when is the hfi for?)
    """
    logger.info(
        "Processing HFI elevation %s for run date: %s, for date: %s", run_type, run_datetime, for_date
    )
    perf_start = perf_counter()

    async with get_async_write_session_scope() as session:
        run_parameters_id = await get_run_parameters_id(session, run_type, run_datetime, for_date)

        stmt = select(AdvisoryTPIStats).where(AdvisoryTPIStats.run_parameters == run_parameters_id)

        exists = (await session.execute(stmt)).scalars().first() is not None
        if not exists:
            fire_zone_stats = await process_tpi_by_firezone(run_type, run_datetime, for_date)
            await store_elevation_tpi_stats(session, run_parameters_id, fire_zone_stats)
        else:
            logger.info("Elevation stats already computed")

    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info("%f delta count before and after processing HFI elevation", delta)


@dataclass(frozen=True)
class FireZoneTPIStats:
    """
    Captures fire zone stats of TPI pixels hitting >4K HFI threshold via
    a dictionary, fire_zone_stats, of {source_identifier: {1: X, 2: Y, 3: Z}}, where 1 = valley bottom, 2 = mid slope, 3 = upper slope
    and X, Y, Z are pixel counts at each of those elevation classes respectively.

    Also includes the TPI raster's pixel size in metres.
    """

    fire_zone_stats: Dict[int, Dict[int, int]]
    pixel_size_metres: int


async def process_tpi_by_firezone(run_type: RunType, run_datetime: datetime, for_date: date):
    """
    Given run parameters, lookup associated snow-masked HFI and static classified TPI geospatial data.
    Cut out each fire zone shape from the above and intersect the TPI and HFI pixels, counting each pixel contributing to the TPI class.
    Capture all fire zone stats keyed by its source_identifier.

    :param run_type: forecast or actual
    :param run_datetime: datetime the sfms file was created
    :param for_date: date the computation is for
    :return: fire zone TPI status
    """

    gdal.SetConfigOption("AWS_SECRET_ACCESS_KEY", config.get("OBJECT_STORE_SECRET"))
    gdal.SetConfigOption("AWS_ACCESS_KEY_ID", config.get("OBJECT_STORE_USER_ID"))
    gdal.SetConfigOption("AWS_S3_ENDPOINT", config.get("OBJECT_STORE_SERVER"))
    gdal.SetConfigOption("AWS_VIRTUAL_HOSTING", "FALSE")
    bucket = config.get("OBJECT_STORE_BUCKET")
    dem_file = config.get("CLASSIFIED_TPI_DEM_NAME")
    key = f"/vsis3/{bucket}/dem/tpi/{dem_file}"
    hfi_raster_filename = get_raster_tif_filename(for_date)
    hfi_raster_key = get_snow_masked_hfi_filepath(run_datetime, run_type, hfi_raster_filename)
    hfi_key = f"/vsis3/{bucket}/{hfi_raster_key}"
    fire_zone_stats: Dict[int, Dict[int, int]] = {}
    with tempfile.TemporaryDirectory() as temp_dir:
        # keep these large intermediate rasters on disk so the worker is not left
        # holding a province-sized GDAL MEM dataset after processing completes.
        warped_hfi_path = os.path.join(temp_dir, f"warp_{hfi_raster_filename}")
        masked_tpi_path = os.path.join(temp_dir, "masked_hfi_tpi.tif")
        pixel_size_metres = 0

        with (
            gdal.Open(key, gdal.GA_ReadOnly) as tpi_source,
            gdal.Open(hfi_key, gdal.GA_ReadOnly) as hfi_source,
        ):
            pixel_size_metres = int(tpi_source.GetGeoTransform()[1])
            resized_hfi_source = warp_to_match_raster(hfi_source, tpi_source, warped_hfi_path)
            masked_tpi_source = None
            try:
                masked_tpi_source = raster_mul(
                    tpi_source, resized_hfi_source, output_path=masked_tpi_path
                )
                masked_tpi_source.FlushCache()
            finally:
                masked_tpi_source = None
                resized_hfi_source = None

        async with get_async_write_session_scope() as session:
            stmt = text("SELECT id, source_identifier FROM public.advisory_shapes;")
            result = await session.execute(stmt)

            with gdal.Open(masked_tpi_path, gdal.GA_ReadOnly) as hfi_masked_tpi:
                hfi_masked_tpi_srs = hfi_masked_tpi.GetSpatialRef()

                for row in result:
                    output_path = os.path.join(temp_dir, f"firezone_{row[1]}.tif")
                    cut_hfi_masked_tpi = None
                    advisory_shape_geom = None
                    zone_tpi_classes = None
                    try:
                        advisory_shape_geom = await get_advisory_shape(
                            session, row[0], hfi_masked_tpi_srs
                        )

                        warp_options = gdal.WarpOptions(
                            format="GTiff",
                            cutlineWKT=advisory_shape_geom,
                            cutlineSRS=advisory_shape_geom.GetSpatialReference(),
                            cropToCutline=True,
                        )
                        cut_hfi_masked_tpi = gdal.Warp(
                            output_path, hfi_masked_tpi, options=warp_options
                        )
                        zone_tpi_classes = cut_hfi_masked_tpi.GetRasterBand(1).ReadAsArray()
                        tpi_classes, counts = np.unique(zone_tpi_classes, return_counts=True)
                        tpi_class_freq_dist = dict(zip(tpi_classes, counts))

                        # Drop TPI class 4, this is the no data value from the TPI raster
                        tpi_class_freq_dist.pop(4, None)
                        fire_zone_stats[row[0]] = tpi_class_freq_dist
                    finally:
                        zone_tpi_classes = None
                        advisory_shape_geom = None
                        cut_hfi_masked_tpi = None

    return FireZoneTPIStats(fire_zone_stats=fire_zone_stats, pixel_size_metres=pixel_size_metres)


async def store_elevation_tpi_stats(
    session: AsyncSession, run_parameters_id: int, fire_zone_tpi_stats: FireZoneTPIStats
):
    """
    Writes elevation TPI statistics to the database.

    :param shape_id: The advisory shape id.
    :param run_parameters_id: The RunParameter object id associated with this run_type, for_date and run_datetime
    :param fire_zone_stats: Dictionary keying shape id to a dictionary of classified tpi hfi pixel counts
    """
    advisory_tpi_stats_list = []
    for shape_id, tpi_freq_count in fire_zone_tpi_stats.fire_zone_stats.items():
        advisory_tpi_stats = AdvisoryTPIStats(
            advisory_shape_id=int(shape_id),
            run_parameters=run_parameters_id,
            valley_bottom=tpi_freq_count.get(1, 0),
            mid_slope=tpi_freq_count.get(2, 0),
            upper_slope=tpi_freq_count.get(3, 0),
            pixel_size_metres=fire_zone_tpi_stats.pixel_size_metres,
        )
        advisory_tpi_stats_list.append(advisory_tpi_stats)

    await save_advisory_elevation_tpi_stats(session, advisory_tpi_stats_list)
