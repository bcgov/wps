"""
Temperature interpolation processor for SFMS.

This processor orchestrates the daily temperature interpolation workflow:
1. Fetch station observations from WF1
2. Interpolate to raster using IDW with elevation adjustment
3. Upload to S3 storage
"""

import logging
import os
import tempfile
from datetime import datetime
from typing import List
import aiofiles
import aiofiles.os
from app.sfms.interpolation_source import StationTemperatureSource
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.utils.s3_client import S3Client
from wps_shared.sfms.raster_addresser import RasterKeyAddresser
from wps_shared.schemas.sfms import SFMSDailyActual
from app.sfms.temperature_interpolation import (
    interpolate_temperature_to_raster,
    get_dem_path,
)
from app.sfms.sfms_common import get_mask_path

logger = logging.getLogger(__name__)


class TemperatureInterpolationProcessor:
    """Processor for interpolating station temperatures to raster format."""

    def __init__(self, datetime_to_process: datetime, raster_addresser: RasterKeyAddresser):
        """
        Initialize the temperature interpolation processor.

        :param datetime_to_process: The datetime to process (typically noon observation time)
        """
        self.datetime_to_process = datetime_to_process
        self.raster_addresser = raster_addresser

    async def process(
        self,
        s3_client: S3Client,
        reference_raster_path: str,
        sfms_actuals: List[SFMSDailyActual],
        temperature_source: StationTemperatureSource,
    ) -> str:
        """
        Process temperature interpolation for the specified datetime.

        :param s3_client: S3Client instance for uploading results
        :param reference_raster_path: Path to reference raster (defines grid properties)
        :return: S3 key of uploaded temperature raster
        """
        logger.info("Starting temperature interpolation for %s", self.datetime_to_process)

        # Configure GDAL for S3 access
        set_s3_gdal_config()

        # Get DEM and mask paths
        dem_path = get_dem_path()
        mask_path = get_mask_path()
        logger.info("Using DEM: %s", dem_path)
        logger.info("Using mask: %s", mask_path)

        if not sfms_actuals:
            raise RuntimeError(f"No station temperatures found for {self.datetime_to_process}")

        logger.info("Processing %d stations with temperature data", len(sfms_actuals))

        station_lats, station_lons, station_values = temperature_source.get_interpolation_data(
            sfms_actuals
        )

        # Generate temporary file path
        temp_dir = tempfile.gettempdir()
        temp_raster_path = os.path.join(
            temp_dir, f"temp_interpolation_{self.datetime_to_process.strftime('%Y%m%d')}.tif"
        )

        try:
            interpolate_temperature_to_raster(
                station_lats,
                station_lons,
                station_values,
                reference_raster_path,
                dem_path,
                temp_raster_path,
                mask_path=mask_path,
            )

            # Upload to S3
            s3_key = self.raster_addresser.get_interpolated_key(
                self.datetime_to_process, temperature_source.weather_param
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
