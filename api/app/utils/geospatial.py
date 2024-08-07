from dataclasses import dataclass
import logging
from typing import Any, Optional
from osgeo import gdal


logger = logging.getLogger(__name__)


def warp_to_match_extent(source_raster: gdal.Dataset, raster_to_match: gdal.Dataset, output_path: str) -> gdal.Dataset:
    """
    Warp the source_raster to match the extent and projection of the other raster.

    :param source_raster: the raster to warp
    :param raster_to_match: the reference raster to match the source against
    :param output_path: output path of the resulting raster
    :return: warped raster dataset
    """
    source_geotransform = raster_to_match.GetGeoTransform()
    x_res = source_geotransform[1]
    y_res = -source_geotransform[5]
    minx = source_geotransform[0]
    maxy = source_geotransform[3]
    maxx = minx + source_geotransform[1] * raster_to_match.RasterXSize
    miny = maxy + source_geotransform[5] * raster_to_match.RasterYSize
    extent = [minx, miny, maxx, maxy]

    # Warp to match input option parameters
    return gdal.Warp(output_path, source_raster, dstSRS=raster_to_match.GetProjection(), outputBounds=extent, xRes=x_res, yRes=y_res, resampleAlg=gdal.GRA_NearestNeighbour)


def raster_mul(tpi_raster: gdal.Dataset, hfi_raster: gdal.Dataset, chunk_size=256) -> gdal.Dataset:
    """
    Multiply rasters together by reading in chunks of pixels at a time to avoid loading
    the rasters into memory all at once.

    :param tpi_raster: Classified TPI raster to multiply against the classified HFI raster
    :param hfi_raster: Classified HFI raster to multiply against the classified TPI raster
    :raises ValueError: Raised if the dimensions of the rasters don't match
    :return: Multiplied raster result as a raster dataset
    """
    # Get raster dimensions
    x_size = tpi_raster.RasterXSize
    y_size = tpi_raster.RasterYSize

    # Check if the dimensions of both rasters match
    if x_size != hfi_raster.RasterXSize or y_size != hfi_raster.RasterYSize:
        raise ValueError("The dimensions of the two rasters do not match.")

    # Get the geotransform and projection from the first raster
    geotransform = tpi_raster.GetGeoTransform()
    projection = tpi_raster.GetProjection()

    # Create the output raster
    driver = gdal.GetDriverByName("MEM")
    out_raster: gdal.Dataset = driver.Create("memory", x_size, y_size, 1, gdal.GDT_Byte)

    # Set the geotransform and projection
    out_raster.SetGeoTransform(geotransform)
    out_raster.SetProjection(projection)

    # Process in chunks
    for y in range(0, y_size, chunk_size):
        y_chunk_size = min(chunk_size, y_size - y)

        for x in range(0, x_size, chunk_size):
            x_chunk_size = min(chunk_size, x_size - x)

            # Read chunks from both rasters
            tpi_chunk = tpi_raster.GetRasterBand(1).ReadAsArray(x, y, x_chunk_size, y_chunk_size)
            hfi_chunk = hfi_raster.GetRasterBand(1).ReadAsArray(x, y, x_chunk_size, y_chunk_size)

            hfi_chunk[hfi_chunk >= 1] = 1
            hfi_chunk[hfi_chunk < 1] = 0

            # Multiply the chunks
            tpi_chunk *= hfi_chunk

            # Write the result to the output raster
            out_raster.GetRasterBand(1).WriteArray(tpi_chunk, x, y)
            tpi_chunk = None
            hfi_chunk = None

    return out_raster
