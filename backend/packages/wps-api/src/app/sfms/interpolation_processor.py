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
from app.sfms.interpolation_source import StationInterpolationSource
from wps_shared.schemas.sfms import SFMSDailyActual
from app.sfms.weather_interpolation import (
    interpolate_to_raster,
)
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.utils.s3_client import S3Client
from wps_shared.sfms.raster_addresser import (
    RasterKeyAddresser,
    SFMSInterpolatedWeatherParameter,
)

logger = logging.getLogger(__name__)


class InterpolationProcessor:
    """Processor for interpolating station weather values to raster format."""

    def __init__(self, datetime_to_process: datetime, raster_addresser: RasterKeyAddresser):
        """
        Initialize the interpolation processor.

        :param datetime_to_process: The datetime to process (typically noon observation time)
        :param raster_addresser: The raster addresser instance used for addressing SFMS keys

        """
        self.datetime_to_process = datetime_to_process
        self.raster_addresser = raster_addresser

    async def process(
        self,
        s3_client: S3Client,
        reference_raster_path: str,
        sfms_actuals: List[SFMSDailyActual],
        weather_param: SFMSInterpolatedWeatherParameter,
        weather_data_source: StationInterpolationSource,
    ) -> str:
        """
        Process weather parameter interpolation for the specified datetime.

        :param s3_client: S3Client instance for uploading results
        :param reference_raster_path: Path to reference raster (defines grid properties)
        :param sfms_actuals: daily actuals for stations for the date of interest
        :return: S3 key of uploaded temperature raster
        """
        logger.info(
            "Starting interpolation for date: %s and weather parameter: %s ",
            self.datetime_to_process,
            weather_param.value,
        )

        # Configure GDAL for S3 access
        set_s3_gdal_config()

        if not sfms_actuals:
            raise RuntimeError(f"No station actuals found for {self.datetime_to_process}")

        logger.info("Processing %d stations data", len(sfms_actuals))

        # Extract interpolation data
        station_lats, station_lons, station_values = weather_data_source.get_interpolation_data(
            sfms_actuals
        )

        # Generate temporary file path
        temp_dir = tempfile.gettempdir()
        temp_raster_path = os.path.join(
            temp_dir,
            f"{weather_param.value}_interpolation_{self.datetime_to_process.strftime('%Y%m%d')}.tif",
        )

        try:
            interpolate_to_raster(
                station_lats, station_lons, station_values, reference_raster_path, temp_raster_path
            )

            # Upload to S3
            s3_key = self.raster_addresser.get_interpolated_key(
                self.datetime_to_process, weather_param
            )

            logger.info("Uploading raster to S3: %s", s3_key)
            async with aiofiles.open(temp_raster_path, "rb") as f:
                contents = await f.read()
                await s3_client.put_object(key=s3_key, body=contents)

            logger.info("Interpolation complete: %s", s3_key)
            return s3_key

        finally:
            # Clean up temporary file asynchronously
            try:
                await aiofiles.os.remove(temp_raster_path)
            except FileNotFoundError:
                pass  # File doesn't exist, nothing to clean up
