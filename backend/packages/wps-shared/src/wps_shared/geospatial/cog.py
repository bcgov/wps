"""
Cloud Optimized GeoTIFF (COG) utilities.

This module provides functions for reprojecting rasters and generating
Cloud Optimized GeoTIFFs optimized for web delivery.
"""

import logging
from osgeo import gdal

logger = logging.getLogger(__name__)


def reproject_raster(
    input_path: str,
    output_path: str,
    target_srs: str = "EPSG:3857",
    resample_alg: int = gdal.GRA_NearestNeighbour,
    preserve_resolution: bool = True
) -> str:
    """
    Reproject a raster to a target spatial reference system.

    :param input_path: Path to input raster
    :param output_path: Path for output raster
    :param target_srs: Target SRS (default: EPSG:3857 Web Mercator)
    :param resample_alg: GDAL resampling algorithm (default: nearest neighbor)
    :param preserve_resolution: Preserve pixel resolution from source (default: True)
    :return: Path to output raster
    """
    src_ds = gdal.Open(input_path)
    if not src_ds:
        raise ValueError(f"Failed to open input raster: {input_path}")

    # Get source resolution if preserving
    if preserve_resolution:
        gt = src_ds.GetGeoTransform()
        xres = gt[1]  # pixel width
        yres = abs(gt[5])  # pixel height
        warp_options = {
            "xRes": xres,
            "yRes": yres
        }
    else:
        warp_options = {}

    logger.info(f"Reprojecting {input_path} to {target_srs}")
    gdal.Warp(
        output_path,
        input_path,
        dstSRS=target_srs,
        resampleAlg=resample_alg,
        format="GTiff",
        **warp_options
    )

    logger.info(f"Reprojection complete: {output_path}")
    src_ds = None
    return output_path


def generate_cloud_optimized_geotiff(
    input_path: str,
    output_path: str,
    compression: str = "LZW",
    resampling: str = "NEAREST",
    blocksize: int = 512
) -> str:
    """
    Generate a Cloud Optimized GeoTIFF (COG) from an input raster.

    COGs are optimized for efficient web delivery with:
    - Internal tiling for random access
    - Overviews (pyramids) for different zoom levels
    - Compression to reduce file size

    :param input_path: Path to input raster
    :param output_path: Path for output COG
    :param compression: Compression algorithm (LZW, DEFLATE, etc.)
    :param resampling: Resampling method for overviews (NEAREST, BILINEAR, etc.)
    :param blocksize: Internal tile size (default: 512)
    :return: Path to output COG
    """
    src_ds = gdal.Open(input_path)
    if not src_ds:
        raise ValueError(f"Failed to open input raster: {input_path}")

    cog_options = [
        f"COMPRESS={compression}",
        f"BLOCKSIZE={blocksize}",
        "OVERVIEWS=IGNORE_EXISTING",  # Always create new overviews
        f"RESAMPLING={resampling}",
    ]

    logger.info(f"Generating COG: {output_path}")
    cog_driver = gdal.GetDriverByName("COG")
    if not cog_driver:
        raise RuntimeError("COG driver not available. Ensure GDAL >= 3.1")

    cog_driver.CreateCopy(output_path, src_ds, options=cog_options)
    logger.info(f"COG created: {output_path}")

    src_ds = None
    return output_path


def generate_web_optimized_cog(
    input_path: str,
    output_path: str,
    target_srs: str = "EPSG:3857",
    temp_dir: str | None = None,
    resample_alg: int = gdal.GRA_NearestNeighbour,
    compression: str = "LZW"
) -> str:
    """
    One-step function to reproject and generate a web-optimized COG.

    This is a convenience function that combines reprojection and COG generation.
    Useful for converting rasters to web-ready format in a single call.

    :param input_path: Path to input raster (any projection)
    :param output_path: Path for final COG output
    :param target_srs: Target SRS (default: EPSG:3857 Web Mercator)
    :param temp_dir: Directory for intermediate files (default: same as output)
    :param resample_alg: GDAL resampling algorithm
    :param compression: Compression algorithm for COG
    :return: Path to output COG
    """
    import os
    from tempfile import NamedTemporaryFile

    # Determine temp file location
    if temp_dir:
        temp_file = os.path.join(temp_dir, "reprojected_temp.tif")
    else:
        output_dir = os.path.dirname(output_path) or "."
        temp_file = os.path.join(output_dir, "reprojected_temp.tif")

    try:
        # Step 1: Reproject to target SRS
        logger.info(f"Step 1/2: Reprojecting to {target_srs}")
        reproject_raster(
            input_path,
            temp_file,
            target_srs=target_srs,
            resample_alg=resample_alg
        )

        # Step 2: Generate COG
        logger.info("Step 2/2: Generating COG")
        generate_cloud_optimized_geotiff(
            temp_file,
            output_path,
            compression=compression,
            resampling="NEAREST" if resample_alg == gdal.GRA_NearestNeighbour else "BILINEAR"
        )

        return output_path
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
