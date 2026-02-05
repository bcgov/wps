"""
Relative humidity interpolation using Inverse Distance Weighting (IDW) with elevation adjustment.

This module implements the SFMS relative humidity interpolation workflow:
1. Interpolate dew point temperatures to a raster using IDW with elevation adjustment
   (same lapse rate approach as temperature)
2. Read the already-interpolated temperature raster
3. Compute RH from temperature and dew point using the Magnus formula
"""

import logging
import numpy as np
from osgeo import gdal
from wps_sfms.interpolation.source import StationDewPointSource, StationTemperatureSource
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.spatial_interpolation import idw_interpolation
from wps_sfms.interpolation.common import (
    SFMS_NO_DATA,
    log_interpolation_stats,
)

logger = logging.getLogger(__name__)

# Environmental lapse rate: 6.5°C per 1000m elevation (average observed rate)
# Applied to both temperature and dew point
LAPSE_RATE = 0.0065

# Magnus formula constants for RH calculation
MAGNUS_ALPHA = 17.625
MAGNUS_BETA = 243.04


def compute_rh_from_temp_and_dewpoint(
    temp: np.ndarray, dewpoint: np.ndarray
) -> np.ndarray:
    """
    Compute relative humidity from temperature and dew point using the Magnus formula.

    RH = 100 * exp((MAGNUS_ALPHA * Td) / (Td + MAGNUS_BETA)) /
                exp((MAGNUS_ALPHA * T) / (T + MAGNUS_BETA))

    :param temp: Temperature array in Celsius
    :param dewpoint: Dew point temperature array in Celsius
    :return: Relative humidity as percentage (0-100), clamped
    """
    rh = 100.0 * (
        np.exp((MAGNUS_ALPHA * dewpoint) / (dewpoint + MAGNUS_BETA))
        / np.exp((MAGNUS_ALPHA * temp) / (temp + MAGNUS_BETA))
    )
    return np.clip(rh, 0.0, 100.0).astype(np.float32)


def interpolate_rh_to_raster(
    dewpoint_source: StationDewPointSource,
    temperature_raster_path: str,
    reference_raster_path: str,
    dem_path: str,
    output_path: str,
    mask_path: str,
) -> str:
    """
    Interpolate relative humidity to a raster by:
    1. Interpolating dew point with elevation adjustment (same as temperature)
    2. Reading the already-interpolated temperature raster
    3. Computing RH from the two using the Magnus formula

    :param dewpoint_source: StationDewPointSource with station dew point data
    :param temperature_raster_path: Path to already-interpolated temperature raster
    :param reference_raster_path: Path to reference raster (defines grid)
    :param dem_path: Path to DEM raster for elevation adjustment
    :param output_path: Path to write output RH raster
    :param mask_path: Path to BC mask raster (0 = masked, non-zero = valid)
    :return: Path to output raster
    """

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

            # Read the already-interpolated temperature raster
            with WPSDataset(temperature_raster_path) as temp_ds:
                temp_band: gdal.Band = temp_ds.ds.GetRasterBand(1)
                temp_data = temp_band.ReadAsArray()
                temp_nodata = temp_band.GetNoDataValue()
                if temp_data is None:
                    raise ValueError("Failed to read temperature raster data")

            rh_array = np.full((y_size, x_size), SFMS_NO_DATA, dtype=np.float32)

            # Use BC mask to determine valid pixels
            with WPSDataset(mask_path) as mask_ds:
                valid_mask = ref_ds.apply_mask(mask_ds.warp_to_match(ref_ds))

            lats, lons, valid_yi, valid_xi = dem_ds.get_lat_lon_coords(valid_mask)
            valid_elevations = dem_data[valid_mask]

            total_pixels = x_size * y_size
            skipped_nodata_count = total_pixels - len(valid_yi)

            logger.info("Interpolating dew point for RH raster grid (%d x %d)", x_size, y_size)
            logger.info(
                "Processing %d valid pixels (skipping %d NoData pixels)",
                len(valid_yi),
                skipped_nodata_count,
            )

            station_lats, station_lons, sea_level_dewpoints = (
                dewpoint_source.get_interpolation_data()
            )
            logger.info(
                "Running batch dew point IDW interpolation for %d pixels and %d stations",
                len(lats),
                len(station_lats),
            )

            interpolated_sea_level_dewpoints = idw_interpolation(
                lats, lons, station_lats, station_lons, sea_level_dewpoints
            )
            assert isinstance(interpolated_sea_level_dewpoints, np.ndarray)

            interpolation_succeeded = ~np.isnan(interpolated_sea_level_dewpoints)
            interpolated_count = int(np.sum(interpolation_succeeded))
            failed_interpolation_count = len(interpolated_sea_level_dewpoints) - interpolated_count

            rows = valid_yi[interpolation_succeeded]
            cols = valid_xi[interpolation_succeeded]

            # Adjust dew point from sea level back to actual elevation
            sea = interpolated_sea_level_dewpoints[interpolation_succeeded].astype(
                np.float32, copy=False
            )
            elev = valid_elevations[interpolation_succeeded].astype(np.float32, copy=False)
            actual_dewpoints = StationTemperatureSource.compute_adjusted_temps(sea, elev, LAPSE_RATE)

            # Get corresponding temperature values from the interpolated temp raster
            temp_values = temp_data[rows, cols].astype(np.float32)

            # Only compute RH where both temp and dew point are valid
            temp_valid = temp_values != temp_nodata if temp_nodata is not None else np.ones_like(temp_values, dtype=bool)
            both_valid = temp_valid

            if np.any(both_valid):
                rh_values = compute_rh_from_temp_and_dewpoint(
                    temp_values[both_valid], actual_dewpoints[both_valid]
                )
                rh_array[rows[both_valid], cols[both_valid]] = rh_values

        log_interpolation_stats(
            total_pixels, interpolated_count, failed_interpolation_count, skipped_nodata_count
        )

        WPSDataset.from_array(
            array=rh_array,
            geotransform=geo_transform,
            projection=projection,
            nodata_value=SFMS_NO_DATA,
            datatype=gdal.GDT_Float32,
        ).export_to_geotiff(output_path)

        logger.info("RH interpolation complete: %s", output_path)
        return output_path
