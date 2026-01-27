"""
Temperature interpolation using Inverse Distance Weighting (IDW) with elevation adjustment.

This module implements the SFMS temperature interpolation workflow:
1. Fetch station data from WF1
2. Adjust station temperatures to sea level using dry adiabatic lapse rate
3. Interpolate adjusted temperatures to raster using IDW
4. Adjust raster cell temperatures back to actual elevation using DEM
"""

import logging
import numpy as np
from osgeo import gdal
from wps_sfms.interpolation.source import StationTemperatureSource
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.spatial_interpolation import idw_interpolation
from wps_sfms.interpolation.common import (
    log_interpolation_stats,
)

logger = logging.getLogger(__name__)

# Environmental lapse rate: 6.5°C per 1000m elevation (average observed rate)
# This matches the CWFIS implementation
LAPSE_RATE = 0.0065


def interpolate_temperature_to_raster(
    temperature_source: StationTemperatureSource,
    reference_raster_path: str,
    dem_path: str,
    output_path: str,
    mask_path: str,
) -> str:
    """
    Interpolate station temperatures to a raster using IDW and elevation adjustment.

    :param temperature_source: StationTemperatureSource,
    :param reference_raster_path: Path to reference raster (defines grid)
    :param dem_path: Path to DEM raster for elevation adjustment
    :param output_path: Path to write output temperature raster
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

            temp_array = np.full((y_size, x_size), -9999.0, dtype=np.float32)

            # Use BC mask to determine valid pixels
            with WPSDataset(mask_path) as mask_ds:
                valid_mask = ref_ds.apply_mask(mask_ds)

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

            station_lats, station_lons, sea_level_temps = (
                temperature_source.get_interpolation_data()
            )
            logger.info(
                "Running batch temperature IDW interpolation for %d pixels and %d stations",
                len(lats),
                len(station_lats),
            )

            interpolated_sea_level_temps = idw_interpolation(
                lats, lons, station_lats, station_lons, sea_level_temps
            )
            assert isinstance(interpolated_sea_level_temps, np.ndarray)

            interpolation_succeeded = ~np.isnan(interpolated_sea_level_temps)
            interpolated_count = int(np.sum(interpolation_succeeded))
            failed_interpolation_count = len(interpolated_sea_level_temps) - interpolated_count

            rows = valid_yi[interpolation_succeeded]
            cols = valid_xi[interpolation_succeeded]

            # Keep dtype consistent with temp_array (float32) to avoid up/down casts
            sea = interpolated_sea_level_temps[interpolation_succeeded].astype(
                np.float32, copy=False
            )
            elev = valid_elevations[interpolation_succeeded].astype(np.float32, copy=False)

            actual_temps = temperature_source.compute_adjusted_temps(sea, elev, LAPSE_RATE)

            # Write the results directly into the output raster
            temp_array[rows, cols] = actual_temps

        log_interpolation_stats(
            total_pixels, interpolated_count, failed_interpolation_count, skipped_nodata_count
        )

        WPSDataset.from_array(
            array=temp_array,
            geotransform=geo_transform,
            projection=projection,
            nodata_value=-9999.0,
            datatype=gdal.GDT_Float32,
        ).export_to_geotiff(output_path)

        logger.info("Temperature interpolation complete: %s", output_path)
        return output_path
