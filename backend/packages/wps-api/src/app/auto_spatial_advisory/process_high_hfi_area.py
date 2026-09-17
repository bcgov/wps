"""Calculate high-HFI area per fire zone from aligned rasters."""

import logging
from collections import Counter
from datetime import date, datetime
from time import perf_counter

import numpy as np
from sqlalchemy import select
from wps_shared.db.crud.auto_spatial_advisory import (
    get_advisory_shape_ids_by_source_identifier,
    get_hfi_threshold_ids,
    get_run_parameters_id,
)
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import (
    HfiClassificationThresholdEnum,
    HighHfiArea,
)
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.zonal_stats import (
    count_values_by_zone,
    iter_raster_windows,
    pixel_area,
)
from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import BaseRasterAddresser, S3Key
from wps_shared.utils.s3 import gdal_s3_context

from app.auto_spatial_advisory.hfi_filepath import (
    get_raster_tif_filename,
    get_snow_masked_hfi_filepath,
)

logger = logging.getLogger(__name__)

CLASS_NAMES = {
    1: HfiClassificationThresholdEnum.ADVISORY.value,
    2: HfiClassificationThresholdEnum.WARNING.value,
}


def count_high_hfi_pixels(
    counts: Counter[tuple[int, int]],
    zones: np.ndarray,
    hfi: np.ndarray,
    zone_nodata: float | int,
) -> None:
    """Merge one window's advisory and warning pixel counts into the running totals."""
    valid_zone = zones != zone_nodata
    mask = valid_zone & np.isin(hfi, tuple(CLASS_NAMES))
    counts.update(count_values_by_zone(zones, hfi, mask))


def calculate_high_hfi_raster_areas(
    zone_path: str, classified_hfi_path: str
) -> dict[tuple[int, int], float]:
    """Return areas keyed by zone source identifier and classified-HFI value.

    Exact pixel counts are accumulated across bounded windows before being multiplied by the
    projected area represented by one pixel.
    """
    counts: Counter[tuple[int, int]] = Counter()
    with WPSDataset(zone_path) as zones, WPSDataset(classified_hfi_path) as hfi:
        area_per_pixel = pixel_area(zones.ds)
        zone_nodata = zones.ds.GetRasterBand(1).GetNoDataValue()
        for window in iter_raster_windows([zones.ds, hfi.ds]):
            count_high_hfi_pixels(counts, *window.arrays, zone_nodata)
    return {key: count * area_per_pixel for key, count in counts.items()}


async def process_high_hfi_area(run_type: RunType, run_datetime: datetime, for_date: date):
    """Calculate and store advisory and warning HFI area by fire zone from aligned rasters."""
    run_type = RunType(run_type)
    logger.info(
        "Processing high HFI area for run type: %s, run datetime: %s, for date: %s",
        run_type,
        run_datetime,
        for_date,
    )
    perf_start = perf_counter()
    async with get_async_write_session_scope() as session:
        run_parameters_id = await get_run_parameters_id(session, run_type, run_datetime, for_date)
        exists = await session.scalar(
            select(HighHfiArea.id).where(HighHfiArea.run_parameters == run_parameters_id).limit(1)
        )
        if exists is not None:
            logger.info("High HFI area already processed")
            return

        classified_key = get_snow_masked_hfi_filepath(
            run_datetime, run_type, get_raster_tif_filename(for_date)
        )
        raster_addresser = BaseRasterAddresser()
        zone_path = raster_addresser.get_fire_zone_units_path()
        classified_hfi_path = raster_addresser.gdal_path(S3Key(classified_key))
        logger.info("Calculating high HFI area by fire zone from aligned rasters")
        with gdal_s3_context():
            areas = calculate_high_hfi_raster_areas(zone_path, classified_hfi_path)

        shape_ids = await get_advisory_shape_ids_by_source_identifier(session)
        thresholds = await get_hfi_threshold_ids(session)
        logger.info("Writing %d high HFI area records", len(areas))
        session.add_all(
            HighHfiArea(
                advisory_shape_id=shape_ids[source_identifier],
                threshold=thresholds[CLASS_NAMES[hfi_class]],
                run_parameters=run_parameters_id,
                area=area,
            )
            for (source_identifier, hfi_class), area in areas.items()
        )

    logger.info("Processed high HFI area in %.2f seconds", perf_counter() - perf_start)
