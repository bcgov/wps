import os
import pytest
from osgeo import gdal
from pyproj import CRS
from affine import Affine
from wps_shared.geospatial.geospatial import get_transformer
from wps_shared.geospatial.geospatial import NAD83_CRS
from app.c_haines.c_haines_index import BoundingBoxChecker


@pytest.mark.parametrize(
    "grib_file, x_coordinate, y_coordinate, is_inside",
    [
        ("CMC_hrdps_continental_DEPR_ISBL_0850_ps2.5km_2021012618_P048-00.grib2", 1, 1, False),
        ("CMC_hrdps_continental_DEPR_ISBL_0850_ps2.5km_2021012618_P048-00.grib2", 2, 2, False),
        ("CMC_hrdps_continental_DEPR_ISBL_0850_ps2.5km_2021012618_P048-00.grib2", 315, 0, True),
    ],
)
def test_bounding_box(grib_file, x_coordinate, y_coordinate, is_inside):
    dirname = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(dirname, grib_file)
    dataset = gdal.Open(filename, gdal.GA_ReadOnly)

    crs = CRS.from_string(dataset.GetProjection())
    transform = Affine.from_gdal(*dataset.GetGeoTransform())
    raster_to_geo_transformer = get_transformer(crs, NAD83_CRS)

    bounding_box_checker = BoundingBoxChecker(transform, raster_to_geo_transformer)

    assert bounding_box_checker.is_inside(x_coordinate, y_coordinate) == is_inside
