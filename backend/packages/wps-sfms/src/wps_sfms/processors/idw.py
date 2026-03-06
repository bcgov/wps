"""
Interpolation processor for SFMS.

Base class implementing the shared workflow for all IDW-based interpolation:
1. Interpolate station observations to raster
2. Upload to S3 storage

Subclasses override interpolate() for parameter-specific logic
(elevation adjustment, DEM-based corrections, etc.).
"""

import logging
import os
import tempfile
from dataclasses import dataclass

import aiofiles
import numpy as np
from numpy.typing import NDArray
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.spatial_interpolation import idw_interpolation
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.utils.s3_client import S3Client
from wps_sfms.interpolation.idw import interpolate_to_raster
from wps_sfms.interpolation.source import StationInterpolationSource

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ValidPixelIDWResult:
    """Result of IDW interpolation performed on valid raster pixels only."""

    interpolated_values: NDArray[np.float32]
    succeeded_mask: NDArray[np.bool_]
    rows: NDArray[np.intp]
    cols: NDArray[np.intp]
    values: NDArray[np.float32]
    total_pixels: int
    interpolated_count: int
    failed_interpolation_count: int
    skipped_nodata_count: int


def idw_on_valid_pixels(
    valid_lats: NDArray[np.float32],
    valid_lons: NDArray[np.float32],
    valid_yi: NDArray[np.intp],
    valid_xi: NDArray[np.intp],
    station_lats: NDArray[np.float32],
    station_lons: NDArray[np.float32],
    station_values: NDArray[np.float32],
    total_pixels: int,
    label: str,
) -> ValidPixelIDWResult:
    """Run batch IDW interpolation for valid pixels and return indexed results."""
    skipped_nodata_count = total_pixels - len(valid_yi)

    logger.info(
        "Processing %d valid pixels (skipping %d NoData pixels)",
        len(valid_yi),
        skipped_nodata_count,
    )
    logger.info(
        "Running batch %s IDW interpolation for %d pixels and %d stations",
        label,
        len(valid_lats),
        len(station_lats),
    )

    raw_interpolated = idw_interpolation(
        valid_lats, valid_lons, station_lats, station_lons, station_values
    )
    assert isinstance(raw_interpolated, np.ndarray)
    interpolated_values = raw_interpolated.astype(np.float32, copy=False)

    succeeded_mask = ~np.isnan(interpolated_values)
    interpolated_count = int(np.sum(succeeded_mask))
    failed_interpolation_count = len(interpolated_values) - interpolated_count

    rows = valid_yi[succeeded_mask]
    cols = valid_xi[succeeded_mask]
    values = interpolated_values[succeeded_mask].astype(np.float32, copy=False)

    return ValidPixelIDWResult(
        interpolated_values=interpolated_values,
        succeeded_mask=succeeded_mask,
        rows=rows,
        cols=cols,
        values=values,
        total_pixels=total_pixels,
        interpolated_count=interpolated_count,
        failed_interpolation_count=failed_interpolation_count,
        skipped_nodata_count=skipped_nodata_count,
    )


class Interpolator:
    """Base processor: plain IDW interpolation + S3 upload.

    Subclasses override interpolate() to add parameter-specific logic
    such as elevation adjustment or derived quantities.

    This base contract is for scalar-value sources (lats, lons, values).
    Specialized interpolators (for example wind direction) may use a different
    source shape in their own `interpolate()` override.
    """

    def __init__(self, mask_path: str):
        self.mask_path = mask_path

    def interpolate(
        self, source: StationInterpolationSource, reference_raster_path: str
    ) -> WPSDataset:
        lats, lons, values = source.get_interpolation_data()
        return interpolate_to_raster(lats, lons, values, reference_raster_path, self.mask_path)

    async def process(
        self,
        s3_client: S3Client,
        reference_raster_path: str,
        source: object,
        output_key: str,
    ) -> str:
        """
        Interpolate station observations to a raster and upload to S3.

        :param s3_client: S3Client instance for uploading results
        :param reference_raster_path: Path to reference raster (defines grid properties)
        :param source: Station data source for this processor. The expected
            source shape is defined by the concrete `interpolate()` implementation.
        :param output_key: S3 key where the resulting raster will be uploaded
        :return: S3 key of uploaded raster
        """
        set_s3_gdal_config()
        logger.info("Starting interpolation, output: %s", output_key)

        with self.interpolate(source, reference_raster_path) as dataset:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = os.path.join(tmp_dir, os.path.basename(output_key))
                dataset.export_to_geotiff(tmp_path)

                async with aiofiles.open(tmp_path, "rb") as f:
                    await s3_client.put_object(key=output_key, body=await f.read())

        logger.info("Interpolation complete: %s", output_key)
        return output_key
