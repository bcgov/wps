"""
Temperature interpolation processor for SFMS.

This processor orchestrates the daily temperature interpolation workflow:
1. Fetch station observations from WF1
2. Interpolate to raster using IDW with elevation adjustment
3. Upload to S3 storage
"""

import logging
import tempfile
from datetime import datetime
from typing import List
from aiohttp import ClientSession
from wps_shared.wildfire_one.wildfire_fetchers import fetch_access_token
from wps_shared.stations import get_stations_from_source
from wps_shared.schemas.stations import WeatherStation
from wps_shared.utils.s3 import set_s3_gdal_config
from app.sfms.temperature_interpolation import (
    fetch_station_temperatures,
    interpolate_temperature_to_raster,
    get_interpolated_temp_key,
    upload_raster_to_s3,
    get_dem_path
)

logger = logging.getLogger(__name__)


class TemperatureInterpolationProcessor:
    """Processor for interpolating station temperatures to raster format."""

    def __init__(self, datetime_to_process: datetime):
        """
        Initialize the temperature interpolation processor.

        :param datetime_to_process: The datetime to process (typically noon observation time)
        """
        self.datetime_to_process = datetime_to_process

    async def process(self, reference_raster_path: str) -> str:
        """
        Process temperature interpolation for the specified datetime.

        :param reference_raster_path: Path to reference raster (defines grid properties)
        :return: S3 key of uploaded temperature raster
        """
        logger.info("Starting temperature interpolation for %s", self.datetime_to_process)

        # Configure GDAL for S3 access
        set_s3_gdal_config()

        # Get DEM path
        dem_path = await get_dem_path()
        logger.info("Using DEM: %s", dem_path)

        # Fetch station metadata (including elevation)
        stations = await self._fetch_stations()
        logger.info("Retrieved %d stations", len(stations))

        # Fetch temperature observations from WF1
        async with ClientSession() as session:
            auth_headers = await self._get_auth_headers(session)
            station_temps = await fetch_station_temperatures(
                session,
                auth_headers,
                self.datetime_to_process,
                stations
            )

        if not station_temps:
            raise RuntimeError(f"No station temperatures found for {self.datetime_to_process}")

        logger.info("Processing %d stations with temperature data", len(station_temps))

        # Interpolate to raster
        with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp_file:
            temp_raster_path = tmp_file.name

        try:
            await interpolate_temperature_to_raster(
                station_temps,
                reference_raster_path,
                dem_path,
                temp_raster_path
            )

            # Upload to S3
            s3_key = get_interpolated_temp_key(self.datetime_to_process)
            await upload_raster_to_s3(temp_raster_path, s3_key)

            logger.info("Temperature interpolation complete: %s", s3_key)
            return s3_key

        finally:
            # Clean up temporary file
            import os
            if os.path.exists(temp_raster_path):
                os.unlink(temp_raster_path)

    async def _fetch_stations(self) -> List[WeatherStation]:
        """
        Fetch all weather stations with metadata (including elevation).

        :return: List of WeatherStation objects with elevation data
        """
        # Fetch from WFWX source (includes elevation data)
        all_stations = await get_stations_from_source()

        # Filter to only stations with elevation data
        stations_with_elevation = [
            station for station in all_stations
            if station.elevation is not None
        ]

        logger.info(
            "Filtered %d stations with elevation data from %d total stations",
            len(stations_with_elevation),
            len(all_stations)
        )

        return stations_with_elevation

    async def _get_auth_headers(self, session: ClientSession) -> dict:
        """
        Get authentication headers for WF1 API.

        :param session: aiohttp ClientSession
        :return: Dictionary of headers
        """
        token_response = await fetch_access_token(session)
        access_token = token_response.get("access_token")

        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
