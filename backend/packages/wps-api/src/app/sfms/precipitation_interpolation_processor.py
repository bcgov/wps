"""
Precipitation interpolation processor for SFMS.

This processor orchestrates the daily precipitation interpolation workflow:
1. Fetch station observations from WF1
2. Interpolate to raster using IDW
3. Upload to S3 storage
"""

import logging
import os
import tempfile
from datetime import datetime
from typing import List
import aiofiles
import aiofiles.os
from aiohttp import ClientSession
from wps_shared.schemas.sfms import StationPrecipitation
from app.sfms.precipitation_interpolation import (
    fetch_station_precipitation,
    interpolate_precipitation_to_raster,
)
from wps_shared.wildfire_one.wfwx_api import get_auth_header
from wps_shared.stations import get_stations_from_source
from wps_shared.schemas.stations import WeatherStation
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.utils.s3_client import S3Client
from wps_shared.sfms.raster_addresser import (
    RasterKeyAddresser,
    SFMSInterpolatedWeatherParameter,
)

logger = logging.getLogger(__name__)


class PrecipitationInterpolationProcessor:
    """Processor for interpolating station precipitations to raster format."""

    def __init__(self, datetime_to_process: datetime, raster_addresser: RasterKeyAddresser):
        """
        Initialize the precipitation interpolation processor.

        :param datetime_to_process: The datetime to process (typically noon observation time)
        """
        self.datetime_to_process = datetime_to_process
        self.raster_addresser = raster_addresser

    async def process(self, s3_client: S3Client, reference_raster_path: str) -> str:
        """
        Process precipitation interpolation for the specified datetime.

        :param s3_client: S3Client instance for uploading results
        :param reference_raster_path: Path to reference raster (defines grid properties)
        :return: S3 key of uploaded temperature raster
        """
        logger.info("Starting precipitation interpolation for %s", self.datetime_to_process)

        # Configure GDAL for S3 access
        set_s3_gdal_config()

        # Fetch station metadata (including elevation)
        stations = await self._fetch_stations()
        logger.info("Retrieved %d stations", len(stations))

        # Fetch temperature observations from WF1
        async with ClientSession() as session:
            auth_headers = await get_auth_header(session)
            station_precips = await fetch_station_precipitation(
                session, auth_headers, self.datetime_to_process, stations
            )

        if not station_precips:
            raise RuntimeError(f"No station precipitations found for {self.datetime_to_process}")

        logger.info("Processing %d stations with precipitation data", len(station_precips))

        # Extract interpolation data
        station_lats, station_lons, station_values = StationPrecipitation.get_interpolation_data(station_precips)

        # Generate temporary file path
        temp_dir = tempfile.gettempdir()
        temp_raster_path = os.path.join(
            temp_dir, f"precip_interpolation_{self.datetime_to_process.strftime('%Y%m%d')}.tif"
        )

        try:
            interpolate_precipitation_to_raster(
                station_lats, station_lons, station_values, reference_raster_path, temp_raster_path
            )

            # Upload to S3
            s3_key = self.raster_addresser.get_interpolated_key(
                self.datetime_to_process, SFMSInterpolatedWeatherParameter.PRECIP
            )

            logger.info("Uploading raster to S3: %s", s3_key)
            async with aiofiles.open(temp_raster_path, "rb") as f:
                contents = await f.read()
                await s3_client.put_object(key=s3_key, body=contents)

            logger.info("Temperature interpolation complete: %s", s3_key)
            return s3_key

        finally:
            # Clean up temporary file asynchronously
            try:
                await aiofiles.os.remove(temp_raster_path)
            except FileNotFoundError:
                pass  # File doesn't exist, nothing to clean up

    async def _fetch_stations(self) -> List[WeatherStation]:
        """
        Fetch all weather stations with metadata (including elevation).

        :return: List of WeatherStation objects with elevation data
        """
        # Fetch from WFWX source (includes elevation data)
        all_stations = await get_stations_from_source()

        return all_stations
