import logging
from typing import Tuple
from osgeo import gdal, ogr, osr


logger = logging.getLogger(__name__)


def warp_to_match_extent(source_ds: gdal.Dataset, ds_to_match: gdal.Dataset, output_path: str) -> gdal.Dataset:
    """
    Warp the source dataset to match the extent and projection of the other dataset.

    :param source_ds: the dataset raster to warp
    :param ds_to_match: the reference dataset raster to match the source against
    :param output_path: output path of the resulting raster
    :return: warped raster dataset
    """
    source_geotransform = ds_to_match.GetGeoTransform()
    x_res = source_geotransform[1]
    y_res = -source_geotransform[5]
    minx = source_geotransform[0]
    maxy = source_geotransform[3]
    maxx = minx + source_geotransform[1] * ds_to_match.RasterXSize
    miny = maxy + source_geotransform[5] * ds_to_match.RasterYSize
    extent = [minx, miny, maxx, maxy]

    # Warp to match input option parameters
    return gdal.Warp(output_path, source_ds, dstSRS=ds_to_match.GetProjection(), outputBounds=extent, xRes=x_res, yRes=y_res, resampleAlg=gdal.GRA_NearestNeighbour)


def raster_mul(tpi_ds: gdal.Dataset, hfi_ds: gdal.Dataset, chunk_size=256) -> gdal.Dataset:
    """
    Multiply rasters together by reading in chunks of pixels at a time to avoid loading
    the rasters into memory all at once.

    :param tpi_ds: Classified TPI dataset raster to multiply against the classified HFI dataset raster
    :param hfi_ds: Classified HFI dataset raster to multiply against the classified TPI dataset raster
    :raises ValueError: Raised if the dimensions of the rasters don't match
    :return: Multiplied raster result as a raster dataset
    """
    # Get raster dimensions
    x_size = tpi_ds.RasterXSize
    y_size = tpi_ds.RasterYSize

    # Check if the dimensions of both rasters match
    if x_size != hfi_ds.RasterXSize or y_size != hfi_ds.RasterYSize:
        raise ValueError("The dimensions of the two rasters do not match.")

    # Get the geotransform and projection from the first raster
    geotransform = tpi_ds.GetGeoTransform()
    projection = tpi_ds.GetProjection()

    # Create the output raster
    driver = gdal.GetDriverByName("MEM")
    out_ds: gdal.Dataset = driver.Create("memory", x_size, y_size, 1, gdal.GDT_Byte)

    # Set the geotransform and projection
    out_ds.SetGeoTransform(geotransform)
    out_ds.SetProjection(projection)

    tpi_raster_band = tpi_ds.GetRasterBand(1)
    hfi_raster_band = hfi_ds.GetRasterBand(1)

    # Process in chunks
    for y in range(0, y_size, chunk_size):
        y_chunk_size = min(chunk_size, y_size - y)

        for x in range(0, x_size, chunk_size):
            x_chunk_size = min(chunk_size, x_size - x)

            # Read chunks from both rasters
            tpi_chunk = tpi_raster_band.ReadAsArray(x, y, x_chunk_size, y_chunk_size)
            hfi_chunk = hfi_raster_band.ReadAsArray(x, y, x_chunk_size, y_chunk_size)

            hfi_chunk[hfi_chunk >= 1] = 1
            hfi_chunk[hfi_chunk < 1] = 0

            # Multiply the chunks
            tpi_chunk *= hfi_chunk

            # Write the result to the output raster
            out_ds.GetRasterBand(1).WriteArray(tpi_chunk, x, y)
            tpi_chunk = None
            hfi_chunk = None

    return out_ds


class PointTransformer:
    """
    Transforms the coordinates of a point from one spatial reference to another.
    """

    def __init__(self, source_srs, target_srs):
        source = osr.SpatialReference()
        source.ImportFromEPSG(source_srs)
        target = osr.SpatialReference()
        target.ImportFromEPSG(target_srs)
        self.transform = osr.CoordinateTransformation(source, target)

    def transform_coordinate(self, x: float, y: float) -> Tuple[float, float]:
        point = ogr.CreateGeometryFromWkt(f"POINT ({x} {y})")
        point.Transform(self.transform)
        return (point.GetX(), point.GetY())
