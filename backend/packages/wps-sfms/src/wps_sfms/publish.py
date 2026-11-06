"""Shared helpers for publishing raster outputs and their derived COGs."""

import hashlib
import logging
import os
import tempfile
from dataclasses import dataclass

import aiofiles
import numpy as np
from numpy.typing import NDArray
from wps_shared.geospatial.cog import generate_web_optimized_cog
from wps_shared.geospatial.geospatial import GDALResamplingMethod
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.sfms.raster_addresser import GDALPath, S3Key
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.utils.s3_client import S3Client

from wps_sfms.non_fuel_cog import generate_non_fuel_cog
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PublishedRaster:
    """Storage locations for a published GeoTIFF and its derived COG."""

    output_key: S3Key
    cog_key: GDALPath | None
    content_hash: str
    """sha256 of the uploaded GeoTIFF, as ``S3Client.get_content_hash`` would compute it."""


async def publish_dataset(
    s3_client: S3Client,
    dataset: WPSDataset,
    output_key: S3Key | str,
    generate_cog: bool = True,
    cog_resample_alg: GDALResamplingMethod = GDALResamplingMethod.BILINEAR,
    *,
    cog_non_fuel_mask: NDArray[np.bool_] | None = None,
) -> PublishedRaster:
    """Upload a GeoTIFF and generate its web COG, optionally excluding Non-fuel.

    ``cog_non_fuel_mask`` identifies Non-fuel/water pixels on the dataset's grid.
    It affects only the COG, not the uploaded GeoTIFF or its content hash.
    """

    # The masked COG helper uses bilinear resampling; do not silently ignore another method.
    if cog_non_fuel_mask is not None and cog_resample_alg != GDALResamplingMethod.BILINEAR:
        raise ValueError("Non-fuel COGs require bilinear continuous-data resampling")

    raster_addresser = SFMSNGRasterAddresser()
    s3_output_key = S3Key(str(output_key))
    cog_key = raster_addresser.get_cog_key(s3_output_key) if generate_cog else None

    set_s3_gdal_config()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = os.path.join(tmp_dir, os.path.basename(s3_output_key))
        # Publish the original values before applying any COG-only masking.
        dataset.export_to_geotiff(tmp_path)

        logger.info("Writing raster to S3: %s", s3_output_key)
        async with aiofiles.open(tmp_path, "rb") as f:
            body = await f.read()
        await s3_client.put_object(key=s3_output_key, body=body)

        if cog_key is not None and cog_non_fuel_mask is not None:
            # Exclude classified Non-fuel/water, not every zero; valid fuel zeros still contribute.
            generate_non_fuel_cog(tmp_path, cog_key, cog_non_fuel_mask)
        elif cog_key is not None:
            generate_web_optimized_cog(
                input_path=tmp_path, output_path=cog_key, resample_alg=cog_resample_alg
            )

    return PublishedRaster(
        output_key=s3_output_key,
        cog_key=cog_key,
        content_hash=hashlib.sha256(body).hexdigest(),
    )
