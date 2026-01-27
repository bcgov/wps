"""
Common utilities for SFMS interpolation modules.
"""

import logging


logger = logging.getLogger(__name__)


def log_interpolation_stats(
    total_pixels: int,
    interpolated_count: int,
    failed_interpolation_count: int,
    skipped_nodata_count: int,
) -> None:
    """
    Log interpolation statistics.

    :param total_pixels: Total number of pixels in the raster
    :param interpolated_count: Number of successfully interpolated pixels
    :param failed_interpolation_count: Number of pixels that failed interpolation
    :param skipped_nodata_count: Number of pixels skipped due to NoData
    """
    logger.info("Interpolation complete:")
    logger.info("  Total pixels: %d", total_pixels)
    logger.info(
        "  Successfully interpolated: %d (%.1f%%)",
        interpolated_count,
        100.0 * interpolated_count / total_pixels if total_pixels > 0 else 0,
    )
    logger.info(
        "  Failed interpolation (no stations in range): %d (%.1f%%)",
        failed_interpolation_count,
        100.0 * failed_interpolation_count / total_pixels if total_pixels > 0 else 0,
    )
    logger.info(
        "  Skipped (NoData): %d (%.1f%%)",
        skipped_nodata_count,
        100.0 * skipped_nodata_count / total_pixels if total_pixels > 0 else 0,
    )

    if interpolated_count == 0:
        logger.warning(
            "WARNING: No pixels were successfully interpolated! Check station locations and coordinate system."
        )
