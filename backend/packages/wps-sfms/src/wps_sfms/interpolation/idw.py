"""
Generic IDW (Inverse Distance Weighting) interpolation for SFMS.

Interpolates station observations to a raster grid using IDW.
"""

import logging
from typing import List
import numpy as np
from osgeo import gdal
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.spatial_interpolation import idw_interpolation
from wps_sfms.interpolation.common import (
    SFMS_NO_DATA,
    log_interpolation_stats,
)
from wps_sfms.interpolation.grid import build_grid_context

logger = logging.getLogger(__name__)


def interpolate_to_raster(
    station_lats: List[float],
    station_lons: List[float],
    station_values: List[float],
    reference_raster_path: str,
    mask_path: str,
) -> WPSDataset:
    """
    Interpolate station values to a raster using IDW.

    :param station_lats: List of station latitudes
    :param station_lons: List of station longitudes
    :param station_values: List of values to interpolate
    :param reference_raster_path: Path to reference raster (defines grid)
    :param mask_path: Path to BC mask raster (0 = masked, non-zero = valid)
    :return: In-memory WPSDataset containing interpolated values
    """
    logger.info("Starting interpolation for %d stations", len(station_lats))

    grid = build_grid_context(reference_raster_path, mask_path)

    logger.info("Interpolating for raster grid (%d x %d)", grid.x_size, grid.y_size)
    logger.info(
        "Processing %d valid pixels (skipping %d NoData pixels)",
        len(grid.valid_yi),
        grid.skipped_nodata_count,
    )

    logger.info(
        "Running batch IDW interpolation for %d pixels and %d stations",
        len(grid.valid_lats),
        len(station_lats),
    )
    station_lats_array = np.array(station_lats)
    station_lons_array = np.array(station_lons)
    station_values_array = np.array(station_values)

    interpolated_values = idw_interpolation(
        grid.valid_lats,
        grid.valid_lons,
        station_lats_array,
        station_lons_array,
        station_values_array,
    )
    assert isinstance(interpolated_values, np.ndarray)

    output_array = np.full((grid.y_size, grid.x_size), SFMS_NO_DATA, dtype=np.float32)

    interpolation_succeeded = ~np.isnan(interpolated_values)
    interpolated_count = int(np.sum(interpolation_succeeded))
    failed_interpolation_count = len(interpolated_values) - interpolated_count

    output_array[
        grid.valid_yi[interpolation_succeeded], grid.valid_xi[interpolation_succeeded]
    ] = interpolated_values[interpolation_succeeded]

    log_interpolation_stats(
        grid.total_pixels,
        interpolated_count,
        failed_interpolation_count,
        grid.skipped_nodata_count,
    )

    if interpolated_count == 0:
        raise RuntimeError(
            f"No pixels were successfully interpolated from {len(station_lats)} station(s). "
            "Check that station coordinates fall within the raster extent and that at least "
            "one station has a valid value for this parameter."
        )

    return WPSDataset.from_array(
        array=output_array,
        geotransform=grid.geotransform,
        projection=grid.projection,
        nodata_value=SFMS_NO_DATA,
        datatype=gdal.GDT_Float32,
    )
