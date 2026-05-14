"""Shared helpers for publishing raster outputs and their derived COGs."""

import logging
import os
import tempfile
from dataclasses import dataclass

import aiofiles

from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser
from wps_shared.geospatial.cog import generate_web_optimized_cog
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.sfms.raster_addresser import GDALPath, S3Key
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.utils.s3_client import S3Client

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PublishedRaster:
    """Storage locations for a published GeoTIFF and its derived COG."""

    output_key: S3Key
    cog_key: GDALPath | None


async def publish_dataset(
    s3_client: S3Client,
    dataset: WPSDataset,
    output_key: S3Key | str,
    generate_cog: bool = True,
) -> PublishedRaster:
    """Upload a GeoTIFF to object storage and optionally generate a matching web COG."""

    raster_addresser = SFMSNGRasterAddresser()
    s3_output_key = S3Key(str(output_key))
    cog_key = raster_addresser.get_cog_key(s3_output_key) if generate_cog else None

    set_s3_gdal_config()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = os.path.join(tmp_dir, os.path.basename(s3_output_key))
        dataset.export_to_geotiff(tmp_path)

        logger.info("Writing raster to S3: %s", s3_output_key)
        async with aiofiles.open(tmp_path, "rb") as f:
            await s3_client.put_object(key=s3_output_key, body=await f.read())

        if cog_key is not None:
            generate_web_optimized_cog(input_path=tmp_path, output_path=cog_key)

    return PublishedRaster(output_key=s3_output_key, cog_key=cog_key)
