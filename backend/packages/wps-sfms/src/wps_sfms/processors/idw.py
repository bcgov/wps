"""
Interpolation processor for SFMS.

Base class implementing the shared workflow for all IDW-based interpolation:
1. Interpolate station observations to raster
2. Upload to S3 storage

Subclasses override _interpolate() for parameter-specific logic
(elevation adjustment, DEM-based corrections, etc.).
"""

import logging
import os
import tempfile

import aiofiles
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.utils.s3_client import S3Client
from wps_sfms.interpolation.precipitation import interpolate_to_raster
from wps_sfms.interpolation.source import StationInterpolationSource

logger = logging.getLogger(__name__)


class InterpolationProcessor:
    """Base processor: plain IDW interpolation + S3 upload.

    Subclasses override _interpolate() to add parameter-specific logic
    such as elevation adjustment or derived quantities.
    """

    def __init__(self, mask_path: str):
        self.mask_path = mask_path

    def _interpolate(
        self, source: StationInterpolationSource, reference_raster_path: str, output_path: str
    ) -> None:
        lats, lons, values = source.get_interpolation_data()
        interpolate_to_raster(lats, lons, values, reference_raster_path, output_path, self.mask_path)

    async def process(
        self,
        s3_client: S3Client,
        reference_raster_path: str,
        source: StationInterpolationSource,
        output_key: str,
    ) -> str:
        """
        Interpolate station observations to a raster and upload to S3.

        :param s3_client: S3Client instance for uploading results
        :param reference_raster_path: Path to reference raster (defines grid properties)
        :param source: Station data source providing interpolation inputs
        :param output_key: S3 key where the resulting raster will be uploaded
        :return: S3 key of uploaded raster
        """
        set_s3_gdal_config()
        logger.info("Starting interpolation, output: %s", output_key)

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = os.path.join(tmp_dir, os.path.basename(output_key))
            self._interpolate(source, reference_raster_path, tmp_path)

            async with aiofiles.open(tmp_path, "rb") as f:
                await s3_client.put_object(key=output_key, body=await f.read())

        logger.info("Interpolation complete: %s", output_key)
        return output_key
