"""
Classifies relative topographic position raster into valley bottom, mid slope, upper slope classifications.
"""

import asyncio
import os

import numpy as np
from osgeo import gdal
from wps_shared import config
from wps_shared.utils.s3 import get_client

CLASSIFIED_TPI_FILENAME = "bc_dem_50m_tpi_win100_classified.tif"
CLASSIFICATION_BINS = [-1, -1 / 3, 1 / 3, 1]
CLASSIFIED_TPI_NODATA = 4
GEOTIFF_CREATION_OPTIONS = [
    "TILED=YES",
    "BLOCKXSIZE=256",
    "BLOCKYSIZE=256",
    "COMPRESS=DEFLATE",
    "BIGTIFF=IF_SAFER",
]


def write_classified_tpi(source: gdal.Dataset, target_path: str) -> str:
    """Classify a TPI dataset and write a tiled GeoTIFF for windowed S3 reads."""
    source_band = source.GetRasterBand(1)
    classified = np.digitize(source_band.ReadAsArray(), CLASSIFICATION_BINS)

    if os.path.exists(target_path):
        os.remove(target_path)
    target = gdal.GetDriverByName("GTiff").Create(
        target_path,
        xsize=source_band.XSize,
        ysize=source_band.YSize,
        bands=1,
        eType=gdal.GDT_Byte,
        options=GEOTIFF_CREATION_OPTIONS,
    )
    if target is None:
        raise RuntimeError(f"Failed to create classified TPI raster: {target_path}")

    target.SetGeoTransform(source.GetGeoTransform())
    target.SetProjection(source.GetProjection())
    target_band = target.GetRasterBand(1)
    target_band.SetNoDataValue(CLASSIFIED_TPI_NODATA)
    target_band.WriteArray(classified)
    target_band.FlushCache()
    target = None

    return target_path


async def generate() -> None:
    """Download and classify the 50 m extended BC TPI raster.

    The source raster was generated with WhiteboxTools' Relative Topographic Position Index using
    a window size of 100. Its indices are classified as valley bottom, mid slope, and upper slope
    using the intervals `[-1, -1/3)`, `[-1/3, 1/3)`, and `[1/3, 1)`, respectively. The result is
    written as a local tiled GeoTIFF.
    """
    async with get_client() as (client, bucket):
        tpi_key = f"dem/tpi/{config.get('TPI_DEM_NAME')}"
        response = await client.get_object(Bucket=bucket, Key=tpi_key)
        source_contents = await response["Body"].read()

    source_path = "/vsimem/tpi.tif"
    source = None
    gdal.FileFromMemBuffer(source_path, source_contents)
    try:
        source = gdal.Open(source_path, gdal.GA_ReadOnly)
        if source is None:
            raise RuntimeError(f"Failed to open source TPI raster: {tpi_key}")
        target_path = os.path.join(os.getcwd(), CLASSIFIED_TPI_FILENAME)
        write_classified_tpi(source, target_path)
    finally:
        source = None
        gdal.Unlink(source_path)


if __name__ == "__main__":
    asyncio.run(generate())
