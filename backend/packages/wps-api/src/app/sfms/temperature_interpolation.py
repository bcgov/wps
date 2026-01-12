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
from typing import List, Optional
import numpy as np
from osgeo import gdal, osr
from aiohttp import ClientSession
from wps_shared import config
from wps_shared.wildfire_one.wildfire_fetchers import fetch_raw_dailies_for_all_stations
from wps_shared.wildfire_one.util import is_station_valid
from wps_shared.schemas.stations import WeatherStation
from wps_shared.utils.s3 import get_client

logger = logging.getLogger(__name__)

# Dry adiabatic lapse rate: 9.8°C per 1000m elevation (or 0.0098°C per meter)
DRY_ADIABATIC_LAPSE_RATE = 0.0098

# IDW parameters
IDW_POWER = 2.0  # Standard IDW power parameter
SEARCH_RADIUS = 200000  # 200km search radius in meters


class StationTemperature:
    """Represents a weather station with temperature and location data."""

    def __init__(self, code: int, lat: float, lon: float, elevation: float, temperature: float):
        self.code = code
        self.lat = lat
        self.lon = lon
        self.elevation = elevation
        self.temperature = temperature
        self.sea_level_temp: Optional[float] = None


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


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth.

    :param lat1: Latitude of first point in degrees
    :param lon1: Longitude of first point in degrees
    :param lat2: Latitude of second point in degrees
    :param lon2: Longitude of second point in degrees
    :return: Distance in meters
    """
    # Convert to radians
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)

    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))

    # Earth radius in meters
    radius = 6371000
    return radius * c


def idw_interpolation(
    target_lat: float,
    target_lon: float,
    stations: List[StationTemperature],
    power: float = IDW_POWER,
    search_radius: float = SEARCH_RADIUS,
) -> Optional[float]:
    """
    Perform Inverse Distance Weighting interpolation for a single point.

    IDW formula: value = Σ(w_i * v_i) / Σ(w_i)
    where w_i = 1 / (distance_i ^ power)

    :param target_lat: Latitude of point to interpolate
    :param target_lon: Longitude of point to interpolate
    :param stations: List of StationTemperature objects with sea_level_temp set
    :param power: IDW power parameter (default 2.0)
    :param search_radius: Maximum distance to consider stations (meters)
    :return: Interpolated temperature value or None if no stations in range
    """
    if not stations:
        return None

    weights = []
    values = []

    for station in stations:
        if station.sea_level_temp is None:
            continue

        # Calculate distance from target point to station
        distance = haversine_distance(target_lat, target_lon, station.lat, station.lon)

        # Skip stations outside search radius
        if distance > search_radius:
            continue

        # Handle case where point is exactly at station location
        if distance < 1.0:  # Within 1 meter
            return station.sea_level_temp

        # Calculate IDW weight
        weight = 1.0 / (distance**power)
        weights.append(weight)
        values.append(station.sea_level_temp)

    # Check if we found any stations in range
    if not weights:
        return None

    # Calculate weighted average
    total_weight = sum(weights)
    interpolated_value = sum(w * v for w, v in zip(weights, values)) / total_weight

    return interpolated_value


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

    # Open reference raster to get grid properties
    ref_ds: gdal.Dataset = gdal.Open(reference_raster_path, gdal.GA_ReadOnly)
    if ref_ds is None:
        raise RuntimeError(f"Failed to open reference raster: {reference_raster_path}")

    # Get raster properties
    geo_transform = ref_ds.GetGeoTransform()
    projection = ref_ds.GetProjection()
    x_size = ref_ds.RasterXSize
    y_size = ref_ds.RasterYSize

    # Open DEM raster
    dem_ds: gdal.Dataset = gdal.Open(dem_path, gdal.GA_ReadOnly)
    if dem_ds is None:
        raise RuntimeError(f"Failed to open DEM raster: {dem_path}")

    # Read DEM data
    dem_band: gdal.Band = dem_ds.GetRasterBand(1)
    dem_data = dem_band.ReadAsArray()
    dem_nodata = dem_band.GetNoDataValue()

    # Create output raster
    driver: gdal.Driver = gdal.GetDriverByName("GTiff")
    out_ds: gdal.Dataset = driver.Create(
        output_path,
        x_size,
        y_size,
        1,  # Single band
        gdal.GDT_Float32,
        options=["COMPRESS=LZW", "TILED=YES"],
    )
    out_ds.SetGeoTransform(geo_transform)
    out_ds.SetProjection(projection)
    out_band: gdal.Band = out_ds.GetRasterBand(1)
    out_band.SetNoDataValue(-9999.0)

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
                    sea_level_temp = idw_interpolation(lat, lon, stations)

                    if sea_level_temp is not None:
                        # Adjust to actual elevation
                        actual_temp = adjust_temperature_to_elevation(sea_level_temp, elevation)
                        temp_array[yi, xi] = actual_temp

            processed_pixels += (y_end - y) * (x_end - x)

        # Log progress every 10%
        progress = (processed_pixels / total_pixels) * 100
        if progress % 10 < 1:
            logger.info("Interpolation progress: %.1f%%", progress)

    # Write array to raster
    out_band.WriteArray(temp_array)
    out_band.FlushCache()

    # Cleanup
    ref_ds = None
    dem_ds = None
    out_ds = None

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


async def upload_raster_to_s3(local_path: str, s3_key: str) -> None:
    """
    Upload a raster file to S3 object storage.

    :param local_path: Local file path to upload
    :param s3_key: S3 key (path) to upload to
    """
    logger.info("Uploading raster to S3: %s", s3_key)

    async with get_client() as (client, bucket):
        with open(local_path, "rb") as f:
            await client.put_object(
                Bucket=bucket, Key=s3_key, Body=f.read(), ContentType="image/tiff"
            )

    logger.info("Upload complete: %s", s3_key)
