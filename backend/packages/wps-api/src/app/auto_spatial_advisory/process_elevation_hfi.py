"""Takes a classified HFI image and calculates TPI-based elevation statistics associated with advisory areas per fire zone."""

import logging
import os
import tempfile
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from time import perf_counter
from typing import Dict

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from wps_shared import config
from wps_shared.db.crud.auto_spatial_advisory import (
    get_advisory_shape_ids_by_source_identifier,
    get_run_parameters_id,
    save_advisory_elevation_tpi_stats,
)
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import AdvisoryTPIStats
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.zonal_stats import count_values_by_zone
from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import BaseRasterAddresser
from wps_shared.utils.s3 import gdal_s3_context

from app.auto_spatial_advisory.hfi_filepath import (
    get_raster_tif_filename,
    get_snow_masked_hfi_filepath,
)

logger = logging.getLogger(__name__)


async def process_hfi_elevation(run_type: RunType, run_datetime: datetime, for_date: date):
    """Create new elevation based hfi analysis records for the given date.

    :param run_type: The type of run to process. (is it a forecast or actual run?)
    :param run_datetime: The date and time of the sfms run in UTC. (when was the hfi file created?)
    :param for_date: The date of the hfi to process. (when is the hfi for?)
    """
    logger.info(
        "Processing HFI elevation %s for run date: %s, for date: %s",
        run_type,
        run_datetime,
        for_date,
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
    """Capture TPI pixel counts where HFI is at least 4,000, grouped by fire zone.

    `fire_zone_stats` has the form `{advisory_shape_id: {1: X, 2: Y, 3: Z}}`, where 1 is valley
    bottom, 2 is mid slope, 3 is upper slope, and X, Y, and Z are the corresponding pixel counts.
    The pixel size is retained so callers can convert the counts to area.
    """

    fire_zone_stats: Dict[int, Dict[int, int]]
    pixel_size_metres: int


def build_fire_zone_tpi_counts(
    counts: Counter[tuple[int, int]], source_to_shape_id: dict[int, int]
) -> Dict[int, Dict[int, int]]:
    """Map raster counts to shape IDs while retaining shapes with no qualifying pixels."""
    fire_zone_stats = {shape_id: {} for shape_id in source_to_shape_id.values()}
    for (source_identifier, tpi_class), frequency in counts.items():
        fire_zone_stats[source_to_shape_id[source_identifier]][tpi_class] = frequency
    return fire_zone_stats


async def process_tpi_by_firezone(run_type: RunType, run_datetime: datetime, for_date: date):
    """Count elevated-HFI TPI classes by fire zone using aligned rasters.

    The classified HFI and fire-zone rasters are aligned to the static TPI grid, then processed in
    bounded windows. A pixel contributes when it belongs to a fire zone, its classified HFI value is
    nonzero (HFI at least 4000), and its TPI class is 1, 2, or 3.

    :param run_type: forecast or actual
    :param run_datetime: datetime the sfms file was created
    :param for_date: date the computation is for
    :return: fire zone TPI status
    """

    bucket = config.get("OBJECT_STORE_BUCKET")
    dem_file = config.get("CLASSIFIED_TPI_DEM_NAME")
    key = f"/vsis3/{bucket}/dem/tpi/{dem_file}"
    hfi_raster_filename = get_raster_tif_filename(for_date)
    hfi_raster_key = get_snow_masked_hfi_filepath(run_datetime, run_type, hfi_raster_filename)
    hfi_key = f"/vsis3/{bucket}/{hfi_raster_key}"
    zone_path = BaseRasterAddresser().get_fire_zone_units_path()
    with gdal_s3_context(), tempfile.TemporaryDirectory() as temp_dir:
        warped_hfi_path = os.path.join(temp_dir, f"warp_{hfi_raster_filename}")
        warped_zones_path = os.path.join(temp_dir, "warp_fire_zone_units.tif")
        tiled_creation_options = ["TILED=YES", "BLOCKXSIZE=256", "BLOCKYSIZE=256"]

        with (
            WPSDataset(key) as tpi_source,
            WPSDataset(hfi_key) as hfi_source,
            WPSDataset(zone_path) as zone_source,
        ):
            pixel_size_metres = int(tpi_source.ds.GetGeoTransform()[1])
            # keep nearest-neighbour resampling so HFI classes and zone identifiers stay discrete
            warp_start = perf_counter()
            with (
                hfi_source.warp_to_match(
                    tpi_source,
                    output_path=warped_hfi_path,
                    creation_options=tiled_creation_options,
                ) as resized_hfi_source,
            ):
                logger.info("Warped HFI to TPI grid in %.2f seconds", perf_counter() - warp_start)

                zone_warp_start = perf_counter()
                with (
                    zone_source.warp_to_match(
                        tpi_source,
                        output_path=warped_zones_path,
                        creation_options=tiled_creation_options,
                    ) as resized_zone_source,
                ):
                    logger.info(
                        "Warped fire zones to TPI grid in %.2f seconds",
                        perf_counter() - zone_warp_start,
                    )
                    counts: Counter[tuple[int, int]] = Counter()
                    zone_nodata = resized_zone_source.ds.GetRasterBand(1).GetNoDataValue()
                    tpi_band = tpi_source.ds.GetRasterBand(1)
                    zone_band = resized_zone_source.ds.GetRasterBand(1)
                    for window in resized_hfi_source.iter_windows():
                        hfi_classes = window.array
                        positive_hfi = hfi_classes > 0
                        if not np.any(positive_hfi):
                            continue

                        tpi_classes = tpi_band.ReadAsArray(
                            window.x_offset, window.y_offset, window.width, window.height
                        )
                        zone_ids = zone_band.ReadAsArray(
                            window.x_offset, window.y_offset, window.width, window.height
                        )
                        valid_zones = zone_ids != zone_nodata
                        valid_tpi_classes = np.isin(tpi_classes, (1, 2, 3))
                        included_pixels = valid_zones & positive_hfi & valid_tpi_classes
                        counts.update(count_values_by_zone(zone_ids, tpi_classes, included_pixels))

        async with get_async_write_session_scope() as session:
            source_to_shape_id = await get_advisory_shape_ids_by_source_identifier(session)
            fire_zone_stats = build_fire_zone_tpi_counts(counts, source_to_shape_id)

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
