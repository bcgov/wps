"""
Precipitation interpolation using Inverse Distance Weighting (IDW).

This module implements the SFMS precipitation interpolation workflow:
1. Fetch station data from WF1
2. Interpolate precipitation to raster using IDW
"""

import logging
from typing import List
import numpy as np
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.spatial_interpolation import idw_interpolation
from app.sfms.sfms_common import (
    log_interpolation_stats,
    save_raster_to_geotiff,
)

logger = logging.getLogger(__name__)


def interpolate_to_raster(
    station_lats: List[float],
    station_lons: List[float],
    station_values: List[float],
    reference_raster_path: str,
    output_path: str,
) -> str:
    """
    Interpolate station weather data to a raster using IDW.

    :param station_lats: List of station latitudes
    :param station_lons: List of station longitudes
    :param station_values: List of weather values
    :param reference_raster_path: Path to reference raster (defines grid)
    :param output_path: Path to write output weather raster
    :return: Path to output raster
    """
    logger.info("Starting interpolation for %d stations", len(station_lats))

    with WPSDataset(reference_raster_path) as ref_ds:
        geo_transform = ref_ds.ds.GetGeoTransform()
        if geo_transform is None:
            raise ValueError(
                f"Failed to get geotransform from reference raster: {reference_raster_path}"
            )
        projection = ref_ds.ds.GetProjection()
        x_size = ref_ds.ds.RasterXSize
        y_size = ref_ds.ds.RasterYSize

        lats, lons, valid_yi, valid_xi = ref_ds.get_lat_lon_coords()

        total_pixels = x_size * y_size
        skipped_nodata_count = total_pixels - len(valid_yi)

        logger.info("Interpolating for raster grid (%d x %d)", x_size, y_size)
        logger.info(
            "Processing %d valid pixels (skipping %d NoData pixels)",
            len(valid_yi),
            skipped_nodata_count,
        )

        logger.info(
            "Running batch IDW interpolation for %d pixels and %d stations",
            len(lats),
            len(station_lats),
        )
        station_lats_array = np.array(station_lats)
        station_lons_array = np.array(station_lons)
        station_values_array = np.array(station_values)

        interpolated_values = idw_interpolation(
            lats, lons, station_lats_array, station_lons_array, station_values_array
        )
        assert isinstance(interpolated_values, np.ndarray)

        precip_array = np.full((y_size, x_size), -9999.0, dtype=np.float32)

        interpolation_succeeded = ~np.isnan(interpolated_values)
        interpolated_count = int(np.sum(interpolation_succeeded))
        failed_interpolation_count = len(interpolated_values) - interpolated_count

        for idx in np.nonzero(interpolation_succeeded)[0]:
            precip_array[valid_yi[idx], valid_xi[idx]] = interpolated_values[idx]

        log_interpolation_stats(
            total_pixels, interpolated_count, failed_interpolation_count, skipped_nodata_count
        )

        save_raster_to_geotiff(precip_array, geo_transform, projection, output_path)

        logger.info("Interpolation complete: %s", output_path)
        return output_path
