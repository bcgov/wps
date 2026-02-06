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
from wps_sfms.interpolation.source import LAPSE_RATE, StationDewPointSource
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.spatial_interpolation import idw_interpolation
from wps_sfms.interpolation.common import (
    SFMS_NO_DATA,
    log_interpolation_stats,
)

logger = logging.getLogger(__name__)

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
                if temp_data is None:
                    raise ValueError("Failed to read temperature raster data")
                temp_valid_mask = temp_data != SFMS_NO_DATA

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
            actual_dewpoints = dewpoint_source.compute_adjusted_values(sea, elev, LAPSE_RATE)

            # Only compute RH where the temp raster also has valid data
            temp_valid = temp_valid_mask[rows, cols]

            if np.any(temp_valid):
                rh_values = dewpoint_source.compute_rh(
                    temp_data[rows[temp_valid], cols[temp_valid]].astype(np.float32),
                    actual_dewpoints[temp_valid],
                )
                rh_array[rows[temp_valid], cols[temp_valid]] = rh_values

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
