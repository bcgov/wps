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
from wps_shared.utils.s3_client import S3Client
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.spatial_interpolation import idw_interpolation

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


async def interpolate_temperature_to_raster(
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
        with WPSDataset(dem_path) as dem_ds:
            # Get raster properties from reference
            geo_transform = ref_ds.ds.GetGeoTransform()
            projection = ref_ds.ds.GetProjection()
            x_size = ref_ds.ds.RasterXSize
            y_size = ref_ds.ds.RasterYSize

            # Read DEM data
            dem_band: gdal.Band = dem_ds.ds.GetRasterBand(1)
            dem_data = dem_band.ReadAsArray()
            dem_nodata = dem_band.GetNoDataValue()

            # Initialize output array with NoData
            temp_array = np.full((y_size, x_size), -9999.0, dtype=np.float32)

            # Setup coordinate transformation from raster projection to WGS84 (lat/lon)
            source_srs = osr.SpatialReference()
            source_srs.ImportFromWkt(projection)
            target_srs = osr.SpatialReference()
            target_srs.ImportFromEPSG(4326)  # WGS84
            coord_transform = osr.CoordinateTransformation(source_srs, target_srs)

            logger.info("Interpolating temperature for raster grid (%d x %d)", x_size, y_size)

            # Process raster in chunks to show progress
            chunk_size = 100
            total_pixels = x_size * y_size
            processed_pixels = 0

            for y in range(0, y_size, chunk_size):
                y_end = min(y + chunk_size, y_size)

                for x in range(0, x_size, chunk_size):
                    x_end = min(x + chunk_size, x_size)

                    # Process chunk
                    for yi in range(y, y_end):
                        for xi in range(x, x_end):
                            # Get elevation from DEM
                            elevation = dem_data[yi, xi]

                            # Skip NoData cells
                            if dem_nodata is not None and elevation == dem_nodata:
                                continue

                            # Convert pixel coordinates to lat/lon
                            # Pixel center coordinates in raster projection
                            x_coord = geo_transform[0] + (xi + 0.5) * geo_transform[1]
                            y_coord = geo_transform[3] + (yi + 0.5) * geo_transform[5]

                            # Transform to lat/lon
                            lon, lat, _ = coord_transform.TransformPoint(x_coord, y_coord)

                            # Interpolate sea level temperature
                            sea_level_temp = idw_interpolation(
                                lat, lon, station_lats, station_lons, station_values
                            )

                            if sea_level_temp is not None:
                                # Adjust to actual elevation
                                actual_temp = adjust_temperature_to_elevation(
                                    sea_level_temp, elevation
                                )
                                temp_array[yi, xi] = actual_temp

                    processed_pixels += (y_end - y) * (x_end - x)

                # Log progress every 10%
                progress = (processed_pixels / total_pixels) * 100
                if progress % 10 < 1:
                    logger.info("Interpolation progress: %.1f%%", progress)

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


async def get_dem_path() -> str:
    """
    Get the path to the DEM raster from S3.

    :return: GDAL virtual file system path to DEM
    """
    bucket = config.get("OBJECT_STORE_BUCKET")
    dem_name = config.get("DEM_NAME")
    return f"/vsis3/{bucket}/dem/mosaics/{dem_name}"


def get_interpolated_temp_key(datetime_utc: datetime) -> str:
    """
    Generate S3 key for interpolated temperature raster with hierarchical date structure.

    Format: sfms/interpolated/temperature/YYYY/MM/DD/temperature_YYYYMMDD.tif

    :param datetime_utc: UTC datetime for the raster
    :return: S3 key path
    """
    date = datetime_utc.date()
    year = date.year
    month = date.month
    day = date.day
    date_str = date.isoformat().replace("-", "")

    return (
        f"sfms/interpolated/temperature/{year:04d}/{month:02d}/{day:02d}/temperature_{date_str}.tif"
    )


async def upload_raster_to_s3(s3_client: S3Client, local_path: str, s3_key: str) -> None:
    """
    Upload a raster file to S3 object storage.

    :param s3_client: S3Client instance
    :param local_path: Local file path to upload
    :param s3_key: S3 key (path) to upload to
    """
    logger.info("Uploading raster to S3: %s", s3_key)

    with open(local_path, "rb") as f:
        await s3_client.put_object(key=s3_key, body=f.read())

    logger.info("Upload complete: %s", s3_key)
