"""
Weather interpolation processor for SFMS.

This processor orchestrates the daily weather parameter interpolation workflow:
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
from wps_sfms.interpolation.source import StationInterpolationSource
from wps_shared.schemas.sfms import SFMSDailyActual
from wps_sfms.interpolation.precipitation import interpolate_to_raster
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.utils.s3_client import S3Client
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser

logger = logging.getLogger(__name__)


class IDWInterpolationProcessor:
    """Processor for interpolating station weather values to raster format."""

    def __init__(self, datetime_to_process: datetime, raster_addresser: SFMSNGRasterAddresser):
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
        weather_data_source: StationInterpolationSource,
        output_key: str,
    ) -> str:
        """
        Process weather parameter interpolation for the specified datetime.

        :param s3_client: S3Client instance for uploading results
        :param reference_raster_path: Path to reference raster (defines grid properties)
        :param sfms_actuals: daily actuals for stations for the date of interest
        :param output_key: S3 key where the resulting raster will be uploaded
        :return: S3 key of uploaded raster
        """
        logger.info(
            "Starting interpolation for date: %s, output: %s",
            self.datetime_to_process,
            output_key,
        )

        # Configure GDAL for S3 access
        set_s3_gdal_config()

        # Get mask path for BC boundary
        mask_path = self.raster_addresser.get_mask_key()
        logger.info("Using mask: %s", mask_path)

        if not sfms_actuals:
            raise RuntimeError(f"No station actuals found for {self.datetime_to_process}")

        logger.info("Processing %d stations data", len(sfms_actuals))

        # Extract interpolation data
        station_lats, station_lons, station_values = weather_data_source.get_interpolation_data(
            sfms_actuals
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_raster_path = os.path.join(temp_dir, os.path.basename(output_key))

            interpolate_to_raster(
                station_lats,
                station_lons,
                station_values,
                reference_raster_path,
                temp_raster_path,
                mask_path=mask_path,
            )

            logger.info("Uploading raster to S3: %s", output_key)
            async with aiofiles.open(temp_raster_path, "rb") as f:
                contents = await f.read()
                await s3_client.put_object(key=output_key, body=contents)

        logger.info("Interpolation complete: %s", output_key)
        return output_key
