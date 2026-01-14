"""
Temperature interpolation using Inverse Distance Weighting (IDW) with elevation adjustment.

This module implements the SFMS temperature interpolation workflow:
1. Fetch station data from WF1
2. Adjust station temperatures to sea level using dry adiabatic lapse rate
3. Interpolate adjusted temperatures to raster using IDW
4. Adjust raster cell temperatures back to actual elevation using DEM
"""

import logging
from datetime import datetime
from typing import List
import numpy as np
from osgeo import gdal, osr
from aiohttp import ClientSession
from wps_shared import config
from wps_shared.wildfire_one.wildfire_fetchers import fetch_raw_dailies_for_all_stations
from wps_shared.wildfire_one.util import is_station_valid
from wps_shared.schemas.stations import WeatherStation
from wps_shared.schemas.sfms import StationTemperature
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.spatial_interpolation import (
    idw_interpolation_batch,
    haversine_distance_matrix,
)

logger = logging.getLogger(__name__)

# Dry adiabatic lapse rate: 9.8°C per 1000m elevation (or 0.0098°C per meter)
DRY_ADIABATIC_LAPSE_RATE = 0.0098


async def fetch_station_temperatures(
    session: ClientSession,
    headers: dict,
    time_of_interest: datetime,
    stations: List[WeatherStation],
) -> List[StationTemperature]:
    """
    Fetch temperature data from WF1 for all stations with values.

    :param session: aiohttp ClientSession for making requests
    :param headers: Authentication headers for WF1 API
    :param time_of_interest: The datetime to fetch observations for
    :param stations: List of WeatherStation objects with elevation data
    :return: List of StationTemperature objects with valid temperature readings
    """
    logger.info("Fetching station temperatures for %s", time_of_interest)

    # Create a lookup dict for station metadata
    station_lookup = {station.code: station for station in stations}

    # Fetch raw daily observations from WF1
    raw_dailies = await fetch_raw_dailies_for_all_stations(session, headers, time_of_interest)

    station_temps = []
    for raw_daily in raw_dailies:
        try:
            # Parse raw daily data
            station_data = raw_daily.get("stationData")
            if not is_station_valid(station_data):
                continue

            station_code = station_data.get("stationCode")
            temperature = raw_daily.get("temperature")
            record_type = raw_daily.get("recordType", {}).get("id")

            # Only use ACTUAL observations
            if record_type != "ACTUAL":
                continue

            # Get station metadata
            if station_code not in station_lookup:
                logger.debug("Station %s not found in station lookup", station_code)
                continue

            station = station_lookup[station_code]

            # Check if we have temperature and elevation data
            if temperature is None:
                logger.debug("No temperature data for station %s", station_code)
                continue

            if station.elevation is None:
                logger.warning("No elevation data for station %s, skipping", station_code)
                continue

            # Create StationTemperature object
            station_temp = StationTemperature(
                code=station_code,
                lat=station.lat,
                lon=station.long,
                elevation=float(station.elevation),
                temperature=float(temperature),
            )
            station_temps.append(station_temp)

        except Exception as e:
            logger.error("Error processing daily for station: %s", e, exc_info=True)
            continue

    logger.info("Found %d stations with valid temperature data", len(station_temps))
    return station_temps


def adjust_temperature_to_sea_level(station: StationTemperature) -> float:
    """
    Adjust station temperature to sea level (0m elevation) using dry adiabatic lapse rate.

    Temperature decreases by 9.8°C per 1000m of elevation gain.
    To adjust to sea level, we ADD temperature based on elevation:
    T_sea_level = T_station + (elevation * lapse_rate)

    :param station: StationTemperature object with elevation and temperature
    :return: Temperature adjusted to sea level in Celsius
    """
    adjustment = station.elevation * DRY_ADIABATIC_LAPSE_RATE
    sea_level_temp = station.temperature + adjustment
    station.sea_level_temp = sea_level_temp
    return sea_level_temp


def adjust_temperature_to_elevation(sea_level_temp: float, elevation: float) -> float:
    """
    Adjust sea level temperature to actual elevation using dry adiabatic lapse rate.

    Temperature decreases by 9.8°C per 1000m of elevation gain.
    T_elevation = T_sea_level - (elevation * lapse_rate)

    :param sea_level_temp: Temperature at sea level in Celsius
    :param elevation: Elevation in meters
    :return: Temperature adjusted to elevation in Celsius
    """
    adjustment = elevation * DRY_ADIABATIC_LAPSE_RATE
    return sea_level_temp - adjustment


def interpolate_temperature_to_raster(
    stations: List[StationTemperature], reference_raster_path: str, dem_path: str, output_path: str
) -> str:
    """
    Interpolate station temperatures to a raster using IDW and elevation adjustment.

    Workflow:
    1. Adjust all station temperatures to sea level
    2. Create raster grid matching reference raster
    3. For each cell, interpolate sea level temperature using IDW
    4. Adjust interpolated temperature to actual elevation using DEM

    :param stations: List of StationTemperature objects
    :param reference_raster_path: Path to reference raster (defines grid)
    :param dem_path: Path to DEM raster for elevation adjustment
    :param output_path: Path to write output temperature raster
    :return: Path to output raster
    """
    logger.info("Starting temperature interpolation for %d stations", len(stations))

    # Log station locations for debugging
    if stations:
        logger.info("Station locations:")
        for station in stations[:5]:  # Log first 5 stations
            logger.info(
                "  Station %d: lat=%.4f, lon=%.4f, elev=%.1fm, temp=%.1f°C",
                station.code,
                station.lat,
                station.lon,
                station.elevation,
                station.temperature,
            )

    # Adjust all station temperatures to sea level
    for station in stations:
        adjust_temperature_to_sea_level(station)

    # Prepare lists for IDW interpolation
    station_lats = [s.lat for s in stations if s.sea_level_temp is not None]
    station_lons = [s.lon for s in stations if s.sea_level_temp is not None]
    station_values = [s.sea_level_temp for s in stations if s.sea_level_temp is not None]

    logger.info("Using %d stations with valid sea level temperatures", len(station_lats))

    # Open reference raster and DEM using WPSDataset
    with WPSDataset(reference_raster_path) as ref_ds:
        # Get raster properties from reference
        geo_transform = ref_ds.ds.GetGeoTransform()
        if geo_transform is None:
            raise ValueError(
                f"Failed to get geotransform from reference raster: {reference_raster_path}"
            )
        projection = ref_ds.ds.GetProjection()
        x_size = ref_ds.ds.RasterXSize
        y_size = ref_ds.ds.RasterYSize

        # Resample DEM to match reference raster (much faster than per-pixel sampling)
        with WPSDataset(dem_path) as dem_ds:
            logger.info(
                "Resampling DEM from (%d x %d) to match reference (%d x %d)",
                dem_ds.ds.RasterXSize,
                dem_ds.ds.RasterYSize,
                x_size,
                y_size,
            )

            # Warp DEM to match reference raster's extent and resolution
            # Use bilinear resampling for smooth elevation interpolation
            from wps_shared.geospatial.geospatial import GDALResamplingMethod
            import uuid

            # Use GDAL's in-memory virtual file system (faster than temp file on disk)
            vsimem_path = f"/vsimem/temp_dem_resample_{uuid.uuid4().hex}.tif"
            try:
                resampled_dem = dem_ds.warp_to_match(
                    ref_ds, vsimem_path, resample_method=GDALResamplingMethod.BILINEAR
                )

                # Read resampled DEM data
                dem_band: gdal.Band = resampled_dem.ds.GetRasterBand(1)
                dem_data = dem_band.ReadAsArray()
                if dem_data is None:
                    raise ValueError("Failed to read resampled DEM data")
                dem_nodata = dem_band.GetNoDataValue()

                logger.info("DEM resampled successfully, nodata value: %s", dem_nodata)

                # Initialize output array with NoData
                temp_array = np.full((y_size, x_size), -9999.0, dtype=np.float32)

                # Setup coordinate transformation from raster projection to WGS84 (lat/lon)
                source_srs = osr.SpatialReference()
                source_srs.ImportFromWkt(projection)
                target_srs = osr.SpatialReference()
                target_srs.ImportFromEPSG(4326)  # WGS84
                coord_transform = osr.CoordinateTransformation(source_srs, target_srs)

                logger.info("Interpolating temperature for raster grid (%d x %d)", x_size, y_size)
                logger.info(
                    "Geotransform: origin=(%.4f, %.4f), pixel_size=(%.4f, %.4f)",
                    geo_transform[0],
                    geo_transform[3],
                    geo_transform[1],
                    geo_transform[5],
                )
                logger.info(
                    "Projection: %s",
                    projection[:100] + "..." if len(projection) > 100 else projection,
                )

                # Create coordinate grids for all pixels at once (vectorized)
                xi_grid, yi_grid = np.meshgrid(np.arange(x_size), np.arange(y_size))

                # Calculate pixel center coordinates in raster projection (vectorized)
                x_coords = geo_transform[0] + (xi_grid + 0.5) * geo_transform[1]
                y_coords = geo_transform[3] + (yi_grid + 0.5) * geo_transform[5]

                # Filter out NoData pixels using boolean mask
                if dem_nodata is not None:
                    valid_mask = dem_data != dem_nodata
                else:
                    valid_mask = np.ones((y_size, x_size), dtype=bool)

                # Get indices and values for valid pixels only
                valid_yi, valid_xi = np.where(valid_mask)
                valid_x_coords = x_coords[valid_mask]
                valid_y_coords = y_coords[valid_mask]
                valid_elevations = dem_data[valid_mask]

                total_pixels = x_size * y_size
                skipped_nodata_count = total_pixels - len(valid_yi)

                logger.info(
                    "Processing %d valid pixels (skipping %d NoData pixels)",
                    len(valid_yi),
                    skipped_nodata_count,
                )

                # Transform all valid coordinates to lat/lon at once (vectorized)
                # Create list of (x, y) tuples for transformation
                coords_to_transform = [(float(x), float(y)) for x, y in zip(valid_x_coords, valid_y_coords)]

                # TransformPoints expects list of (x, y) or (x, y, z) tuples
                # Returns [(lat, lon, z), ...]
                transformed = coord_transform.TransformPoints(coords_to_transform)

                # Extract lat/lon from transformed coordinates
                lats = np.array([t[0] for t in transformed])
                lons = np.array([t[1] for t in transformed])

                # Log first pixel for debugging
                if len(valid_yi) > 0:
                    logger.info(
                        "First pixel [%d,%d]: x_coord=%.4f, y_coord=%.4f -> lat=%.4f, lon=%.4f, elev=%.1f",
                        valid_xi[0],
                        valid_yi[0],
                        valid_x_coords[0],
                        valid_y_coords[0],
                        lats[0],
                        lons[0],
                        valid_elevations[0],
                    )

                # Pre-compute distance matrix: all pixels to all stations at once
                # This is much faster than computing distances in a loop
                logger.info("Computing distance matrix for %d pixels and %d stations", len(lats), len(station_lats))
                station_lats_array = np.array(station_lats)
                station_lons_array = np.array(station_lons)
                station_values_array = np.array(station_values)

                distances_matrix = haversine_distance_matrix(lats, lons, station_lats_array, station_lons_array)

                # Batch interpolate all pixels at once
                logger.info("Running batch IDW interpolation")
                sea_level_temps = idw_interpolation_batch(distances_matrix, station_values_array)

                # Count successes/failures
                # All arrays (sea_level_temps, valid_elevations, valid_yi, valid_xi) have same length
                # and are aligned - they all correspond to the same N valid pixels
                interpolation_succeeded = ~np.isnan(sea_level_temps)
                interpolated_count = np.sum(interpolation_succeeded)
                failed_interpolation_count = len(sea_level_temps) - interpolated_count

                # Apply elevation adjustment and write to output array
                # Loop only over pixels where interpolation succeeded
                for idx in np.where(interpolation_succeeded)[0]:
                    actual_temp = adjust_temperature_to_elevation(
                        float(sea_level_temps[idx]), float(valid_elevations[idx])
                    )
                    temp_array[valid_yi[idx], valid_xi[idx]] = actual_temp
            finally:
                # Clean up in-memory file (ignore errors if file doesn't exist)
                try:
                    gdal.Unlink(vsimem_path)
                except RuntimeError:
                    logger.debug("File doesn't exist or already cleaned up")

        # Log summary statistics (outside DEM context, inside ref context)
        logger.info("Interpolation complete:")
        logger.info("  Total pixels: %d", total_pixels)
        logger.info(
            "  Successfully interpolated: %d (%.1f%%)",
            interpolated_count,
            100.0 * interpolated_count / total_pixels if total_pixels > 0 else 0,
        )
        logger.info(
            "  Failed interpolation (no stations in range): %d (%.1f%%)",
            failed_interpolation_count,
            100.0 * failed_interpolation_count / total_pixels if total_pixels > 0 else 0,
        )
        logger.info(
            "  Skipped (NoData elevation): %d (%.1f%%)",
            skipped_nodata_count,
            100.0 * skipped_nodata_count / total_pixels if total_pixels > 0 else 0,
        )

        if interpolated_count == 0:
            logger.warning(
                "WARNING: No pixels were successfully interpolated! Check station locations and coordinate system."
            )

        # Create output dataset from array using WPSDataset
        output_ds = WPSDataset.from_array(
            array=temp_array,
            geotransform=geo_transform,
            projection=projection,
            nodata_value=-9999.0,
            datatype=gdal.GDT_Float32,
        )

        # Export to GeoTIFF with compression
        with output_ds:
            output_ds.export_to_geotiff(output_path)

        logger.info("Temperature interpolation complete: %s", output_path)
        return output_path


def get_dem_path() -> str:
    """
    Get the path to the DEM raster from S3.

    :return: GDAL virtual file system path to DEM
    """
    bucket = config.get("OBJECT_STORE_BUCKET")
    dem_name = config.get("DEM_NAME")
    return f"/vsis3/{bucket}/dem/mosaics/{dem_name}"
