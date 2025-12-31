"""
Cloud-Optimized GeoTIFF (COG) generation utilities.

This module provides functions for creating web-optimized COGs from geospatial rasters,
including reprojection to web-friendly coordinate systems like EPSG:3857.
"""

import logging

from osgeo import gdal

from wps_shared.geospatial.geospatial import GDALResamplingMethod

logger = logging.getLogger(__name__)


def generate_web_optimized_cog(
    input_path: str,
    output_path: str,
    target_srs: str = "EPSG:3857",
    compression: str = "LZW",
    resample_alg: GDALResamplingMethod = GDALResamplingMethod.BILINEAR,
) -> str:
    """
    Generate a web-optimized Cloud-Optimized GeoTIFF (COG).

    Reproject the input raster to the target SRS (default: Web Mercator)
    and creates a COG with proper tiling and compression for efficient web delivery.

    The implementation uses an efficient in-memory approach:
    1. Warp to target SRS in memory (no intermediate file)
    2. Translate directly to COG format with auto-generated overviews

    :param input_path: Path to input raster (local or /vsis3/)
    :param output_path: Path for output COG (local or /vsis3/)
    :param target_srs: Target spatial reference system (default: EPSG:3857 - Web Mercator)
    :param compression: Compression algorithm (default: LZW). Options: LZW, DEFLATE, ZSTD, etc.
    :param resample_alg: Resampling algorithm for reprojection (default: Bilinear)
    :return: Path to output COG
    """
    logger.info(f"Generating COG: {input_path} -> {output_path} ({target_srs})")

    src_ds = gdal.Open(input_path)
    if src_ds is None:
        raise ValueError(f"Failed to open input raster: {input_path}")

    # Warp to target SRS in memory (no intermediate file)
    warped = gdal.Warp(
        "",  # Empty string creates in-memory dataset
        src_ds,
        format="MEM",
        dstSRS=target_srs,
        resampleAlg=resample_alg.value,
    )

    if warped is None:
        raise RuntimeError(f"Failed to warp raster to {target_srs}")

    # Translate to COG format with auto-generated overviews
    result = gdal.Translate(
        output_path,
        warped,
        format="COG",
        creationOptions=[
            f"COMPRESS={compression}",
            "BIGTIFF=IF_SAFER",
            "OVERVIEWS=IGNORE_EXISTING",  # Always create new overviews
        ],
    )

    # Clean up
    src_ds = None
    warped = None

    if result is None:
        raise RuntimeError(f"Failed to create COG: {output_path}")

    result = None
    logger.info(f"COG generation complete: {output_path}")

    return output_path
