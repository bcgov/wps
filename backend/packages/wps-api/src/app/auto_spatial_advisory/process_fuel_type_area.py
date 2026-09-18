"""Calculate fuel-type area by HFI threshold and fire-zone raster value."""

import logging
from collections import Counter
from datetime import date, datetime
from time import perf_counter

import numpy as np
from sqlalchemy import select
from wps_shared.db.crud.auto_spatial_advisory import (
    get_advisory_shape_ids_by_source_identifier,
    get_fuel_types_id_dict,
    get_hfi_threshold_ids,
    get_run_parameters_id,
)
from wps_shared.db.crud.fuel_layer import get_fuel_type_raster_by_year
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import (
    AdvisoryFuelStats,
    HfiClassificationThresholdEnum,
    SFMSFuelType,
)
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.zonal_stats import (
    count_values_by_zone,
    iter_raster_windows,
)
from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import BaseRasterAddresser, S3Key
from wps_shared.utils.s3 import gdal_s3_context

from app.auto_spatial_advisory.common import get_hfi_s3_key

logger = logging.getLogger(__name__)

FUEL_TYPE_RASTER_RESOLUTION_IN_METRES = 2000
ADVISORY_NAME = HfiClassificationThresholdEnum.ADVISORY.value
WARNING_NAME = HfiClassificationThresholdEnum.WARNING.value


def classify_by_threshold(source_data: np.ndarray, threshold: int) -> np.ndarray:
    """Classify raw HFI values into one advisory threshold mask."""
    if threshold == 1:
        classified = (source_data >= 4000) & (source_data < 10000)
    else:
        classified = source_data >= 10000
    return np.where(np.isfinite(source_data), classified, False).astype(np.int8)


def calculate_fuel_type_areas(
    source: WPSDataset, fuel_types: list[SFMSFuelType]
) -> dict[int, float]:
    """Calculate the combustible area for each SFMS fuel type in a raster."""
    area_per_pixel = source.pixel_area
    histogram = source.ds.GetRasterBand(1).GetHistogram(approx_ok=0)
    areas = {}
    for fuel_type in fuel_types:
        fuel_type_id = fuel_type.fuel_type_id
        if 0 < fuel_type_id < 99:
            area = histogram[fuel_type_id] * area_per_pixel
            if area > 0:
                areas[fuel_type_id] = area
    return areas


def count_fuel_type_hfi_pixels(
    counts: Counter[tuple[int, str, int]],
    zones: np.ndarray,
    raw_hfi: np.ndarray,
    fuel_types: np.ndarray,
    zone_nodata: float | int,
) -> None:
    """Merge one window's combustible-fuel counts by zone and raw-HFI threshold."""
    valid_zone = zones != zone_nodata
    combustible = (fuel_types > 0) & (fuel_types < 99)
    thresholds = {
        ADVISORY_NAME: (raw_hfi >= 4000) & (raw_hfi < 10000),
        WARNING_NAME: raw_hfi >= 10000,
    }
    for threshold_name, threshold_mask in thresholds.items():
        mask = valid_zone & combustible & threshold_mask
        zone_value_counts = count_values_by_zone(zones, fuel_types, mask)
        for (source_identifier, fuel_type), frequency in zone_value_counts.items():
            counts[(source_identifier, threshold_name, fuel_type)] += frequency


def calculate_fuel_type_hfi_areas(
    zone_path: str, raw_hfi_path: str, fuel_path: str
) -> dict[tuple[int, str, int], float]:
    """Return fuel areas keyed by zone source ID, HFI threshold name, and fuel code.

    Counts are accumulated across aligned raster windows and converted to square metres using the
    projected area of one zone-raster pixel.
    """
    counts: Counter[tuple[int, str, int]] = Counter()
    with (
        WPSDataset(zone_path) as zones,
        WPSDataset(raw_hfi_path) as raw_hfi,
        WPSDataset(fuel_path) as fuel,
    ):
        area_per_pixel = zones.pixel_area
        zone_nodata = zones.ds.GetRasterBand(1).GetNoDataValue()
        for window in iter_raster_windows([zones.ds, raw_hfi.ds, fuel.ds]):
            zone_ids, raw_hfi_values, fuel_codes = window.arrays
            count_fuel_type_hfi_pixels(counts, zone_ids, raw_hfi_values, fuel_codes, zone_nodata)
    return {key: count * area_per_pixel for key, count in counts.items()}


async def process_fuel_type_hfi_by_shape(run_type: RunType, run_datetime: datetime, for_date: date):
    """Store fuel area by fire zone and HFI threshold using raster cells."""
    run_type = RunType(run_type)
    logger.info(
        "Processing fuel type area for run type: %s, run datetime: %s, for date: %s",
        run_type,
        run_datetime,
        for_date,
    )
    perf_start = perf_counter()
    async with get_async_write_session_scope() as session:
        run_parameters_id = await get_run_parameters_id(session, run_type, run_datetime, for_date)
        exists = await session.scalar(
            select(AdvisoryFuelStats.id)
            .where(AdvisoryFuelStats.run_parameters == run_parameters_id)
            .limit(1)
        )
        if exists is not None:
            logger.info("Advisory fuel stats already processed")
            return

        fuel_raster = await get_fuel_type_raster_by_year(session, for_date.year)
        if fuel_raster is None:
            raise RuntimeError(f"No fuel type raster found for {for_date.year}")
        raster_addresser = BaseRasterAddresser()
        logger.info("Calculating fuel type area by fire zone and HFI threshold")
        with gdal_s3_context():
            areas = calculate_fuel_type_hfi_areas(
                raster_addresser.get_fire_zone_units_path(),
                get_hfi_s3_key(run_type, run_datetime, for_date),
                raster_addresser.gdal_path(S3Key(fuel_raster.object_store_path)),
            )

        shape_ids = await get_advisory_shape_ids_by_source_identifier(session)
        thresholds = await get_hfi_threshold_ids(session)
        fuel_type_ids = await get_fuel_types_id_dict(session)
        logger.info("Writing %d calculated fuel type area values", len(areas))
        session.add_all(
            AdvisoryFuelStats(
                advisory_shape_id=shape_ids[source_identifier],
                threshold=thresholds[threshold_name],
                run_parameters=run_parameters_id,
                fuel_type=fuel_type_ids[fuel_type],
                area=area,
                fuel_type_raster_id=fuel_raster.id,
            )
            for (source_identifier, threshold_name, fuel_type), area in areas.items()
            if fuel_type in fuel_type_ids
        )

    logger.info("Processed fuel type area in %.2f seconds", perf_counter() - perf_start)
