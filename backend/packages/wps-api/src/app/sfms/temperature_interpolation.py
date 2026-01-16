"""
Temperature interpolation using Inverse Distance Weighting (IDW) with elevation adjustment.

This module implements the SFMS temperature interpolation workflow:
1. Fetch station data from WF1
2. Adjust station temperatures to sea level using dry adiabatic lapse rate
3. Interpolate adjusted temperatures to raster using IDW
4. Adjust raster cell temperatures back to actual elevation using DEM
"""

import logging
from typing import List, Optional
import numpy as np
from osgeo import gdal
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.spatial_interpolation import idw_interpolation
from app.sfms.sfms_common import (
    log_interpolation_stats,
    save_raster_to_geotiff,
)

logger = logging.getLogger(__name__)

# Environmental lapse rate: 6.5°C per 1000m elevation (average observed rate)
# This matches the CWFIS implementation
LAPSE_RATE = 0.0065


def compute_actual_temperatures(
    sea: np.ndarray, elev: np.ndarray, lapse_rate: float, out_dtype=np.float32
) -> np.ndarray:
    """
    Compute actual temperatures from sea-level temps and elevations:
      T(z) = T0 - z * lapse_rate

    Parameters
    ----------
    sea : array-like
        Sea-level temperatures (C). Broadcastable against `elev`.
    elev : array-like
        Elevations (m). Broadcastable against `sea`.
    lapse_rate : float
        Environmental lapse rate in C per meter (positive = cooling with elevation).
    out_dtype : np.dtype
        Output dtype, default float32 to match raster array.

    Returns
    -------
    np.ndarray
        Actual temperatures with dtype `out_dtype`.
    """
    sea = np.asarray(sea, dtype=out_dtype)
    elev = np.asarray(elev, dtype=out_dtype)
    # Use fused/matched dtype ops to avoid accidental upcasting
    return sea - elev * np.asarray(lapse_rate, dtype=out_dtype)


def interpolate_temperature_to_raster(
    station_lats: List[float],
    station_lons: List[float],
    station_values: List[float],
    reference_raster_path: str,
    dem_path: str,
    output_path: str,
    mask_path: Optional[str] = None,
) -> str:
    """
    Interpolate station temperatures to a raster using IDW and elevation adjustment.

    :param station_lats: List of station latitudes
    :param station_lons: List of station longitudes
    :param station_values: List of sea-level adjusted temperatures
    :param reference_raster_path: Path to reference raster (defines grid)
    :param dem_path: Path to DEM raster for elevation adjustment
    :param output_path: Path to write output temperature raster
    :param mask_path: Optional path to mask raster (0 = masked, non-zero = valid)
    :return: Path to output raster
    """
    logger.info("Starting temperature interpolation for %d stations", len(station_lats))

    with WPSDataset(reference_raster_path) as ref_ds:
        geo_transform = ref_ds.ds.GetGeoTransform()
        if geo_transform is None:
            raise ValueError(
                f"Failed to get geotransform from reference raster: {reference_raster_path}"
            )
        projection = ref_ds.ds.GetProjection()
        x_size = ref_ds.ds.RasterXSize
        y_size = ref_ds.ds.RasterYSize

        with WPSDataset(dem_path) as dem_ds:
            dem_band: gdal.Band = dem_ds.ds.GetRasterBand(1)
            dem_data = dem_band.ReadAsArray()
            if dem_data is None:
                raise ValueError("Failed to read DEM data")

            temp_array = np.full((y_size, x_size), -9999.0, dtype=np.float32)

            valid_mask = dem_ds.get_valid_mask()

            # Apply BC mask if provided
            if mask_path is not None:
                with WPSDataset(mask_path) as mask_ds:
                    bc_mask = ref_ds.apply_mask(mask_ds)
                    valid_mask = valid_mask & bc_mask

            lats, lons, valid_yi, valid_xi = dem_ds.get_lat_lon_coords(valid_mask)
            valid_elevations = dem_data[valid_mask]

            total_pixels = x_size * y_size
            skipped_nodata_count = total_pixels - len(valid_yi)

            logger.info("Interpolating temperature for raster grid (%d x %d)", x_size, y_size)
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

            sea_level_temps = idw_interpolation(
                lats, lons, station_lats_array, station_lons_array, station_values_array
            )
            assert isinstance(sea_level_temps, np.ndarray)

            interpolation_succeeded = ~np.isnan(sea_level_temps)
            interpolated_count = int(np.sum(interpolation_succeeded))
            failed_interpolation_count = len(sea_level_temps) - interpolated_count

            # Apply elevation adjustment and write to output array (vectorized)
            rows = valid_yi[interpolation_succeeded]
            cols = valid_xi[interpolation_succeeded]

            # Keep dtype consistent with temp_array (float32) to avoid up/down casts
            sea = sea_level_temps[interpolation_succeeded].astype(np.float32, copy=False)
            elev = valid_elevations[interpolation_succeeded].astype(np.float32, copy=False)

            # Environmental lapse rate is positive (°C per meter); cooling with elevation is subtraction
            actual_temps = compute_actual_temperatures(sea, elev, LAPSE_RATE, out_dtype=np.float32)

            # Write the results directly into the output raster
            temp_array[rows, cols] = actual_temps

        log_interpolation_stats(
            total_pixels, interpolated_count, failed_interpolation_count, skipped_nodata_count
        )

        save_raster_to_geotiff(temp_array, geo_transform, projection, output_path)

        logger.info("Temperature interpolation complete: %s", output_path)
        return output_path
