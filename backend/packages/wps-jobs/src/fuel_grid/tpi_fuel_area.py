import os
import tempfile
from collections import Counter

import numpy as np

from wps_shared.db.models.auto_spatial_advisory import TPIClassEnum
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.zonal_stats import (
    count_values_by_zone,
    iter_raster_windows,
)
from wps_shared.sfms.raster_addresser import BaseRasterAddresser
from wps_shared.utils.s3 import gdal_s3_context


def calculate_tpi_area_data_for_zone(advisory_shape_id: int, data: np.ndarray, pixel_size: int):
    """Yield classified TPI areas from an already selected zone array."""
    unique_values, counts = np.unique(data, return_counts=True)
    for value, count in zip(unique_values, counts):
        if value in TPIClassEnum:
            yield (advisory_shape_id, TPIClassEnum(value), count * pixel_size * pixel_size)


def calculate_masked_tpi_areas(
    masked_tpi_path: str, zone_raster_path: str | None = None
) -> dict[tuple[int, TPIClassEnum], float]:
    """Return fuel-covered area keyed by zone source ID and TPI class.

    The zone raster is nearest-neighbour warped to the TPI grid so integer identifiers remain
    categorical, then pixel counts are accumulated across aligned windows.
    """
    zone_path = zone_raster_path or BaseRasterAddresser().get_fire_zone_units_path()
    counts: Counter[tuple[int, TPIClassEnum]] = Counter()
    with (
        tempfile.TemporaryDirectory() as temp_dir,
        gdal_s3_context(),
        WPSDataset(zone_path) as zones,
        WPSDataset(masked_tpi_path) as masked_tpi,
    ):
        warped_zone_path = os.path.join(temp_dir, "fire_zone_units_tpi_grid.tif")
        # preserve zone identifiers while aligning them to the separate TPI grid
        with zones.warp_to_match(masked_tpi, output_path=warped_zone_path) as tpi_zones:
            area_per_pixel = masked_tpi.pixel_area
            zone_nodata = tpi_zones.ds.GetRasterBand(1).GetNoDataValue()
            for window in iter_raster_windows([tpi_zones.ds, masked_tpi.ds]):
                zone_data, tpi_data = window.arrays
                mask = (zone_data != zone_nodata) & np.isin(tpi_data, (1, 2, 3))
                pair_counts = count_values_by_zone(zone_data, tpi_data, mask)
                for (source_identifier, tpi_class), frequency in pair_counts.items():
                    counts[(source_identifier, TPIClassEnum(tpi_class))] += frequency
    return {key: count * area_per_pixel for key, count in counts.items()}
