from collections import Counter

import numpy as np

from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.zonal_stats import iter_aligned_raster_windows
from wps_shared.sfms.raster_addresser import BaseRasterAddresser
from wps_shared.utils.s3 import gdal_s3_context


def calculate_combustible_area_by_fire_zone(
    fuel_raster_path: str, zone_raster_path: str | None = None
) -> dict[int, float]:
    """Return combustible area by zone source ID from windowed fuel and zone rasters.

    Fuel codes from 1 through 98 are combustible; zero is background and 99 is non-fuel.
    """
    zone_path = zone_raster_path or BaseRasterAddresser().get_fire_zone_units_path()
    counts: Counter[int] = Counter()
    with gdal_s3_context(), WPSDataset(zone_path) as zones, WPSDataset(fuel_raster_path) as fuel:
        area_per_pixel = fuel.pixel_area
        zone_nodata = zones.ds.GetRasterBand(1).GetNoDataValue()
        for window in iter_aligned_raster_windows(zones, fuel):
            zone_ids, fuel_codes = window.arrays
            mask = (zone_ids != zone_nodata) & (fuel_codes > 0) & (fuel_codes < 99)
            unique_zone_ids, frequencies = np.unique(zone_ids[mask], return_counts=True)
            for source_identifier, frequency in zip(unique_zone_ids, frequencies):
                counts[int(source_identifier)] += int(frequency)
    return {
        source_identifier: count * area_per_pixel for source_identifier, count in counts.items()
    }
