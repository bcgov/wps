from affine import Affine
from enum import Enum
from typing import Tuple
from osgeo import gdal, ogr, osr
from typing import Final
from pyproj import CRS, Transformer

# Some constants that are frequently used when transforming coordinates.

# BCGOV standard is to store everything in NAD83 / BC Albers (EPSG:3005).
NAD83_BC_ALBERS: Final = 3005
# NAD 83 alone (EPSG:4269), uses geographic coordinates.
NAD83: Final = "epsg:4269"
NAD83_CRS: Final = CRS(NAD83)
# De facto standard is to expose data in WGS84 (EPSG:4326).
WGS84: Final = "epsg:4326"
# Web Mercator
WEB_MERCATOR: Final = 3857


class GDALResamplingMethod(Enum):
    """
    See api/app/utils/geospatial-interpolation.md for information about which interpolation method to use for your use case

    """

    NEAREST_NEIGHBOUR = gdal.GRA_NearestNeighbour
    BILINEAR = gdal.GRA_Bilinear
    CUBIC = gdal.GRA_Cubic


def warp_to_match_raster(
    source_ds: gdal.Dataset, ds_to_match: gdal.Dataset, output_path: str, resample_method: GDALResamplingMethod = GDALResamplingMethod.NEAREST_NEIGHBOUR
) -> gdal.Dataset:
    """
    Warp the source dataset to match the extent, pixel size, and projection of the other dataset.

    :param source_ds: the dataset raster to warp
    :param ds_to_match: the reference dataset raster to match the source against
    :param output_path: output path of the resulting raster
    :param resample_method: gdal resampling algorithm
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
    return gdal.Warp(output_path, source_ds, dstSRS=ds_to_match.GetProjection(), outputBounds=extent, xRes=x_res, yRes=y_res, resampleAlg=resample_method.value)


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

    def __init__(self, source_srs: int, target_srs: int):
        source = osr.SpatialReference()
        source.ImportFromEPSG(source_srs)
        target = osr.SpatialReference()
        target.ImportFromEPSG(target_srs)
        self.transform = osr.CoordinateTransformation(source, target)

    def transform_coordinate(self, x: float, y: float) -> Tuple[float, float]:
        point = ogr.CreateGeometryFromWkt(f"POINT ({x} {y})")
        point.Transform(self.transform)
        return (point.GetX(), point.GetY())


def prepare_wkt_geom_for_gdal(wkt_geom: str, source_srs: osr.SpatialReference, target_srs_wkt: osr.SpatialReference = None):
    """
    Given a wkt geometry as a string, convert it to an ogr.Geometry that can be used by gdal. Reproject if desired
    :param wkt_geom: The wky geometry string.
    :param source_srs: The spatial reference to assign to the geometry.
    :return: An osr.Geometry.
    """

    geometry: ogr.Geometry = ogr.CreateGeometryFromWkt(wkt_geom)
    geometry.AssignSpatialReference(source_srs)

    if target_srs_wkt:
        target_srs = osr.SpatialReference()
        target_srs.ImportFromWkt(target_srs_wkt)
        transform = osr.CoordinateTransformation(source_srs, target_srs)
        geometry.Transform(transform)

    return geometry


def rasters_match(raster1: gdal.Dataset, raster2: gdal.Dataset) -> bool:
    """
    Compares two rasters to check if they match in pixel size, extents, and projection.

    :param raster1: Opened gdal dataset for a raster.
    :param raster2: Opened gdal dataset for a raster.
    :return: True if rasters match in pixel size, extents, and projection; False otherwise.
    """
    # Get raster properties
    geotransform1 = raster1.GetGeoTransform()
    geotransform2 = raster2.GetGeoTransform()

    projection1 = raster1.GetProjection()
    projection2 = raster2.GetProjection()

    cols1, rows1 = raster1.RasterXSize, raster1.RasterYSize
    cols2, rows2 = raster2.RasterXSize, raster2.RasterYSize

    # Check pixel size (resolution)
    pixel_size_match = geotransform1[1] == geotransform2[1] and geotransform1[5] == geotransform2[5]

    # Check extent (origin and size)
    extent_match = (
        geotransform1[0] == geotransform2[0]  # Top-left X
        and geotransform1[3] == geotransform2[3]  # Top-left Y
        and cols1 == cols2
        and rows1 == rows2
    )

    # Check projection using osr.SpatialReference
    srs1 = osr.SpatialReference()
    srs2 = osr.SpatialReference()
    srs1.ImportFromWkt(projection1)
    srs2.ImportFromWkt(projection2)

    projection_match = srs1.IsSame(srs2) == 1  # `IsSame()` returns 1 if the projections are equivalent

    return pixel_size_match and extent_match and projection_match

def calculate_geographic_coordinate(point: Tuple[int], transform: Affine, transformer: Transformer):
    """Calculate the geographic coordinates for a given points"""
    x_coordinate, y_coordinate = transform * point
    lon, lat = transformer.transform(x_coordinate, y_coordinate)
    return (lon, lat)


def get_dataset_transform(filename) -> Affine:
    """Get the geometry info (origin and pixel size) of the dataset."""
    with gdal.Open(filename) as ds:
        return Affine.from_gdal(*ds.GetGeoTransform())


def get_transformer(crs_from, crs_to):
    """Get an appropriate transformer - it's super important that always_xy=True
    is specified, otherwise the order in the CRS definition is honoured."""
    return Transformer.from_crs(crs_from, crs_to, always_xy=True)