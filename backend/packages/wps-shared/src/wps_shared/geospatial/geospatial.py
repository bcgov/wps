from enum import Enum
from typing import Final, Tuple

from affine import Affine
from osgeo import gdal, ogr, osr
from pyproj import CRS, Transformer

COMPRESSED_TILED_GEOTIFF_OPTIONS: Final[list[str]] = [
    "TILED=YES",
    "BLOCKXSIZE=256",
    "BLOCKYSIZE=256",
    "COMPRESS=DEFLATE",
    "BIGTIFF=IF_SAFER",
]

# Some constants that are frequently used when transforming coordinates.


class SpatialReferenceSystem(Enum):
    """
    Spatial Reference System (SRS) definitions with EPSG codes.

    Each member provides:
    - code: The EPSG code as an integer (via .value)
    - srs: The SRS string in EPSG format (e.g., "EPSG:3857")
    - epsg: The SRS string in lowercase epsg format (e.g., "epsg:3857")
    """

    # BCGOV standard - NAD83 / BC Albers
    NAD83_BC_ALBERS = 3005
    # NAD 83 - Geographic coordinates
    NAD83 = 4269
    # WGS84 - De facto standard for exposing data
    WGS84 = 4326
    # Web Mercator - Standard for web mapping
    WEB_MERCATOR = 3857

    @property
    def code(self) -> int:
        """Return the EPSG code as an integer."""
        return self.value

    @property
    def srs(self) -> str:
        """Return the SRS string in EPSG format (uppercase), e.g., 'EPSG:3857'."""
        return f"EPSG:{self.value}"

    @property
    def epsg(self) -> str:
        """Return the SRS string in epsg format (lowercase), e.g., 'epsg:3857'."""
        return f"epsg:{self.value}"


# Backwards-compatible constants - prefer using SpatialReferenceSystem enum for new code
NAD83_BC_ALBERS: Final = SpatialReferenceSystem.NAD83_BC_ALBERS.code
NAD83: Final = SpatialReferenceSystem.NAD83.epsg
NAD83_CRS: Final = CRS(SpatialReferenceSystem.NAD83.epsg)
WGS84: Final = SpatialReferenceSystem.WGS84.epsg
WEB_MERCATOR: Final = SpatialReferenceSystem.WEB_MERCATOR.code


class GDALResamplingMethod(Enum):
    """
    See api/app/utils/geospatial-interpolation.md for information about which interpolation method to use for your use case

    """

    NEAREST_NEIGHBOUR = gdal.GRA_NearestNeighbour
    BILINEAR = gdal.GRA_Bilinear
    CUBIC = gdal.GRA_Cubic


def warp_to_match_raster(
    source_ds: gdal.Dataset,
    ds_to_match: gdal.Dataset,
    output_path: str,
    resample_method: GDALResamplingMethod = GDALResamplingMethod.NEAREST_NEIGHBOUR,
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
    return gdal.Warp(
        output_path,
        source_ds,
        dstSRS=ds_to_match.GetProjection(),
        outputBounds=extent,
        xRes=x_res,
        yRes=y_res,
        resampleAlg=resample_method.value,
    )


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


def rasters_match(raster1: gdal.Dataset, raster2: gdal.Dataset) -> bool:
    """
    Compare two rasters to check if their grids and coordinate reference systems match.

    Comparing the complete geotransform covers origin, pixel size, rotation, and skew. CRS WKT
    strings may differ while describing the same system, so spatial references are compared with
    GDAL's semantic ``IsSame`` check.

    :param raster1: Opened gdal dataset for a raster.
    :param raster2: Opened gdal dataset for a raster.
    :return: True if rasters have identical dimensions and geotransforms and equivalent coordinate
        reference systems; False otherwise.
    """
    geotransform1 = raster1.GetGeoTransform()
    geotransform2 = raster2.GetGeoTransform()

    projection1 = raster1.GetProjection()
    projection2 = raster2.GetProjection()

    cols1, rows1 = raster1.RasterXSize, raster1.RasterYSize
    cols2, rows2 = raster2.RasterXSize, raster2.RasterYSize

    geotransform_match = geotransform1 == geotransform2
    dimensions_match = cols1 == cols2 and rows1 == rows2

    # Check projection using osr.SpatialReference
    srs1 = osr.SpatialReference()
    srs2 = osr.SpatialReference()
    srs1.ImportFromWkt(projection1)
    srs2.ImportFromWkt(projection2)

    projection_match = (
        srs1.IsSame(srs2) == 1
    )  # `IsSame()` returns 1 if the projections are equivalent

    return geotransform_match and dimensions_match and projection_match


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


def clear_gdal_runtime_cache():
    """Clear the GDAL cache to free up memory after processing large rasters."""
    gdal.VSICurlClearCache()
