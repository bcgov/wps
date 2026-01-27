"""
Weather interpolation using Inverse Distance Weighting (IDW).

This module implements the SFMS weather interpolation workflow:
1. Create raster grid matching reference raster
2. Interpolate weather values to raster using IDW
"""

import logging
from typing import List, Optional
import numpy as np
from osgeo import gdal
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.spatial_interpolation import idw_interpolation
from wps_sfms.interpolation.common import (
    log_interpolation_stats,
)

logger = logging.getLogger(__name__)


def interpolate_to_raster(
    station_lats: List[float],
    station_lons: List[float],
    station_values: List[float],
    reference_raster_path: str,
    output_path: str,
    mask_path: Optional[str] = None,
) -> str:
    """
    Interpolate station weather data to a raster using IDW.

    :param station_lats: List of station latitudes
    :param station_lons: List of station longitudes
    :param station_values: List of weather values
    :param reference_raster_path: Path to reference raster (defines grid)
    :param output_path: Path to write output weather raster
    :param mask_path: Optional path to mask raster (0 = masked, non-zero = valid)
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

        # Build valid mask from reference raster's nodata
        valid_mask = ref_ds.get_valid_mask()

        # Apply BC mask if provided
        if mask_path is not None:
            with WPSDataset(mask_path) as mask_ds:
                bc_mask = ref_ds.apply_mask(mask_ds)
                valid_mask = valid_mask & bc_mask

        lats, lons, valid_yi, valid_xi = ref_ds.get_lat_lon_coords(valid_mask)

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

        WPSDataset.from_array(
            array=precip_array,
            geotransform=geo_transform,
            projection=projection,
            nodata_value=-9999.0,
            datatype=gdal.GDT_Float32,
        ).export_to_geotiff(output_path)

        logger.info("Interpolation complete: %s", output_path)
        return output_path
