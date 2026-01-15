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
from osgeo import gdal
from aiohttp import ClientSession
from wps_shared import config
from wps_shared.wildfire_one.wildfire_fetchers import fetch_raw_dailies_for_all_stations
from wps_shared.wildfire_one.util import is_station_valid
from wps_shared.schemas.stations import WeatherStation
from wps_shared.schemas.sfms import StationPrecipitation
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.spatial_interpolation import idw_interpolation

logger = logging.getLogger(__name__)


async def fetch_station_precipitation(
    session: ClientSession,
    headers: dict,
    time_of_interest: datetime,
    stations: List[WeatherStation],
) -> List[StationPrecipitation]:
    """
    Fetch precipitation data from WF1 for all stations with values.

    :param session: aiohttp ClientSession for making requests
    :param headers: Authentication headers for WF1 API
    :param time_of_interest: The datetime to fetch observations for
    :param stations: List of WeatherStation objects
    :return: List of StationPrecipitation objects with valid precipitation readings
    """
    logger.info("Fetching station temperatures for %s", time_of_interest)

    # Create a lookup dict for station metadata
    station_lookup = {station.code: station for station in stations}

    # Fetch raw daily observations from WF1
    raw_dailies = await fetch_raw_dailies_for_all_stations(session, headers, time_of_interest)

    station_precips = []
    for raw_daily in raw_dailies:
        try:
            # Parse raw daily data
            station_data = raw_daily.get("stationData")
            if not is_station_valid(station_data):
                continue

            station_code = station_data.get("stationCode")
            precipitation = raw_daily.get("precipitation")
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
            if precipitation is None:
                logger.debug("No precipitation data for station %s", station_code)
                continue

            # Create StationTemperature object
            station_temp = StationPrecipitation(
                code=station_code,
                lat=station.lat,
                lon=station.long,
                precipitation=float(precipitation),
            )
            station_precips.append(station_temp)

        except Exception as e:
            logger.error("Error processing daily for station: %s", e, exc_info=True)
            continue

    logger.info("Found %d stations with valid precipitation data", len(station_precips))
    return station_precips


def interpolate_precipitation_to_raster(
    stations: List[StationPrecipitation],
    reference_raster_path: str,
    output_path: str,
) -> str:
    """
    Interpolate station precipitation to a raster using IDW.

    Workflow:
    1. Create raster grid matching reference raster
    2. For each cell, interpolate precipitation using IDW

    :param stations: List of StationPrecipitation objects
    :param reference_raster_path: Path to reference raster (defines grid)
    :param dem_path: Path to DEM raster for elevation adjustment
    :param output_path: Path to write output precipitation raster
    :return: Path to output raster
    """
    logger.info("Starting precipitation interpolation for %d stations", len(stations))

    # Log station locations for debugging
    if stations:
        logger.info("Station locations:")
        for station in stations[:5]:  # Log first 5 stations
            logger.info(
                "  Station %d: lat=%.4f, lon=%.4f, elev=%.1fm, temp=%.1f°C",
                station.code,
                station.lat,
                station.lon,
                station.precipitation,
            )

    # Prepare lists for IDW interpolation
    station_lats = [s.lat for s in stations if s.precipitation is not None]
    station_lons = [s.lon for s in stations if s.precipitation is not None]
    station_values = [s.precipitation for s in stations if s.precipitation is not None]

    logger.info("Using %d stations with valid sea level temperatures", len(station_lats))

    # Open reference raster using WPSDataset
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

        # Get lat/lon coordinates for valid pixels using WPSDataset
        lats, lons, valid_yi, valid_xi = ref_ds.get_lat_lon_coords()

        total_pixels = x_size * y_size
        skipped_nodata_count = total_pixels - len(valid_yi)

        logger.info("Interpolating temperature for raster grid (%d x %d)", x_size, y_size)
        logger.info(
            "Processing %d valid pixels (skipping %d NoData pixels)",
            len(valid_yi),
            skipped_nodata_count,
        )

        # Batch interpolate all pixels at once
        logger.info(
            "Running batch IDW interpolation for %d pixels and %d stations",
            len(lats),
            len(station_lats),
        )
        station_lats_array = np.array(station_lats)
        station_lons_array = np.array(station_lons)
        station_values_array = np.array(station_values)

        precipitations = idw_interpolation(
            lats, lons, station_lats_array, station_lons_array, station_values_array
        )
        assert isinstance(precipitations, np.ndarray)

        # Count successes/failures
        # All arrays (sea_level_temps, valid_elevations, valid_yi, valid_xi) have same length
        # and are aligned - they all correspond to the same N valid pixels
        interpolation_succeeded = ~np.isnan(precipitations)
        interpolated_count = np.sum(interpolation_succeeded)
        failed_interpolation_count = len(precipitations) - interpolated_count

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
            array=precipitations,
            geotransform=geo_transform,
            projection=projection,
            nodata_value=-9999.0,
            datatype=gdal.GDT_Float32,
        )

        # Export to GeoTIFF with compression
        with output_ds:
            output_ds.export_to_geotiff(output_path)

        logger.info("Precipitation interpolation complete: %s", output_path)
        return output_path
