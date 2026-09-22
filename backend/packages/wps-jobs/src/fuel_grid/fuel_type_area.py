from collections import Counter

import numpy as np

from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.zonal_stats import (
    count_values_by_zone,
    iter_raster_windows,
)
from wps_shared.sfms.raster_addresser import BaseRasterAddresser
from wps_shared.utils.s3 import gdal_s3_context


def calculate_fuel_type_areas_per_zone(
    fuel_raster_path: str, zone_raster_path: str | None = None
) -> dict[tuple[int, int], float]:
    """Return combustible area keyed by zone source ID and fuel code.

    Pixel counts are accumulated across aligned windows and converted using projected pixel area.
    """
    zone_path = zone_raster_path or BaseRasterAddresser().get_fire_zone_units_path()
    counts: Counter[tuple[int, int]] = Counter()
    with gdal_s3_context(), WPSDataset(zone_path) as zones, WPSDataset(fuel_raster_path) as fuel:
        area_per_pixel = fuel.pixel_area
        zone_nodata = zones.ds.GetRasterBand(1).GetNoDataValue()
        for window in iter_raster_windows([zones, fuel]):
            zone_ids, fuel_codes = window.arrays
            mask = (zone_ids != zone_nodata) & (fuel_codes > 0) & (fuel_codes < 99)
            counts.update(count_values_by_zone(zone_ids, fuel_codes, mask))
    return {key: count * area_per_pixel for key, count in counts.items()}
