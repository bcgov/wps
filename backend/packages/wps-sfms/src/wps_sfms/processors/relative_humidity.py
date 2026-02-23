"""
Relative humidity interpolation processor for SFMS.

This processor orchestrates the daily RH interpolation workflow:
1. Interpolate dew point to raster using IDW with elevation adjustment
2. Combine with already-interpolated temperature raster to compute RH
3. Upload to S3 storage
"""

import logging
import os
import tempfile
from datetime import datetime
import aiofiles
import aiofiles.os
from wps_sfms.interpolation.source import StationDewPointSource
from wps_shared.sfms.raster_addresser import RasterKeyAddresser, SFMSInterpolatedWeatherParameter
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.utils.s3_client import S3Client
from wps_sfms.interpolation.relative_humidity import interpolate_rh_to_raster

logger = logging.getLogger(__name__)


class RHInterpolationProcessor:
    """Processor for interpolating station relative humidity to raster format."""

    def __init__(self, datetime_to_process: datetime, raster_addresser: RasterKeyAddresser):
        """
        Initialize the RH interpolation processor.

        :param datetime_to_process: The datetime to process (typically noon observation time)
        :param raster_addresser: The raster addresser instance used for addressing SFMS keys
        """
        self.datetime_to_process = datetime_to_process
        self.raster_addresser = raster_addresser

    async def process(
        self,
        s3_client: S3Client,
        reference_raster_path: str,
        dewpoint_source: StationDewPointSource,
    ) -> str:
        """
        Process RH interpolation for the specified datetime.

        Requires that temperature interpolation has already been run for this date,
        as it reads the interpolated temperature raster from S3.

        :param s3_client: S3Client instance for uploading results
        :param reference_raster_path: Path to reference raster (defines grid properties)
        :param dewpoint_source: StationDewPointSource with station dew point data
        :return: S3 key of uploaded RH raster
        """
        logger.info("Starting RH interpolation for %s", self.datetime_to_process)

        # Configure GDAL for S3 access
        set_s3_gdal_config()

        # Get DEM, mask, and interpolated temperature raster paths
        dem_path = self.raster_addresser.get_dem_key()
        mask_path = self.raster_addresser.get_mask_key()
        temp_raster_key = self.raster_addresser.get_interpolated_key(
            self.datetime_to_process, SFMSInterpolatedWeatherParameter.TEMP
        )
        temp_raster_path = self.raster_addresser.s3_prefix + "/" + temp_raster_key

        logger.info("Using DEM: %s", dem_path)
        logger.info("Using mask: %s", mask_path)
        logger.info("Using interpolated temperature raster: %s", temp_raster_path)

        # Generate temporary file path
        temp_dir = tempfile.gettempdir()
        temp_raster_path_local = os.path.join(
            temp_dir, f"rh_interpolation_{self.datetime_to_process.strftime('%Y%m%d')}.tif"
        )

        try:
            interpolate_rh_to_raster(
                dewpoint_source,
                temp_raster_path,
                reference_raster_path,
                dem_path,
                temp_raster_path_local,
                mask_path=mask_path,
            )

            # Upload to S3
            s3_key = self.raster_addresser.get_interpolated_key(
                self.datetime_to_process, SFMSInterpolatedWeatherParameter.RH
            )

            logger.info("Uploading RH raster to S3: %s", s3_key)
            async with aiofiles.open(temp_raster_path_local, "rb") as f:
                contents = await f.read()
                await s3_client.put_object(key=s3_key, body=contents)

            logger.info("RH interpolation complete: %s", s3_key)
            return s3_key

        finally:
            # Clean up temporary file asynchronously
            try:
                await aiofiles.os.remove(temp_raster_path_local)
            except FileNotFoundError:
                pass  # File doesn't exist, nothing to clean up
