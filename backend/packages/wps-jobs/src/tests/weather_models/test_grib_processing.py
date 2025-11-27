"""Tests for grib file processing"""

import os
import logging
import pytest
from operator import itemgetter
from affine import Affine
from pyproj import CRS
from osgeo import gdal
from wps_shared.geospatial.geospatial import NAD83_CRS
import weather_model_jobs.utils.process_grib as process_grib

logger = logging.getLogger(__name__)


def open_grib_file(filename: str):
    """Open the dataset."""
    grib_path = get_grib_file_path(filename)
    return gdal.Open(grib_path)


def get_grib_file_path(filename: str):
    dirname = os.path.dirname(os.path.realpath(__file__))
    grib_path = os.path.join(dirname, filename)
    return grib_path


def read_file_contents(filename):
    """Given a filename, return json"""
    dirname = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dirname, filename), "r") as file:
        return file.read()


@pytest.mark.parametrize(
    "filename,origin,pixel_size",
    [
        (
            "CMC_glb_RH_TGL_2_latlon.15x.15_2020071300_P000.grib2",
            (-180.075, 90.075),
            (0.15000000000000002, -0.15),
        ),
    ],
)
def test_get_dataset_geometry(filename, origin, pixel_size):
    grib_path = get_grib_file_path(filename)
    dataset_geometry = process_grib.get_dataset_transform(grib_path)
    geotransform = dataset_geometry.to_gdal()
    actual_origin = itemgetter(0, 3)(geotransform)
    actual_pixel_size = itemgetter(1, 5)(geotransform)
    assert actual_origin == origin
    assert actual_pixel_size == pixel_size


@pytest.mark.parametrize(
    "geotransform,wkt_projection_string,geographic_coordinate,raster_coordinate",
    [
        (
            [-2099127.494496938, 2500.0, 0.0, -2099388.521499629, 0.0, -2500.0],
            "CMC_hrdps_continental_ps2.5km_projection_wkt.txt",
            [-120.4816667, 50.6733333],
            (472, 819),
        ),
        (
            [-2099127.494496938, 2500.0, 0.0, -2099388.521499629, 0.0, -2500.0],
            "CMC_hrdps_continental_ps2.5km_projection_wkt.txt",
            [-116.7464000, 49.4358000],
            (572, 897),
        ),
        (
            [-2099127.494496938, 2500.0, 0.0, -2099388.521499629, 0.0, -2500.0],
            "CMC_hrdps_continental_ps2.5km_projection_wkt.txt",
            [-123.2732667, 52.0837700],
            (409, 736),
        ),
        (
            [-180.075, 0.15000000000000002, 0.0, 90.075, 0.0, -0.15],
            "CMC_glb_latlon.15x.15_projection_wkt.txt",
            [-120.4816667, 50.6733333],
            (397, 262),
        ),
        (
            [-180.075, 0.15000000000000002, 0.0, 90.075, 0.0, -0.15],
            "CMC_glb_latlon.15x.15_projection_wkt.txt",
            [-116.7464000, 49.4358000],
            (422, 270),
        ),
        (
            [-180.075, 0.15000000000000002, 0.0, 90.075, 0.0, -0.15],
            "CMC_glb_latlon.15x.15_projection_wkt.txt",
            [-123.2732667, 52.0837700],
            (378, 253),
        ),
    ],
)
def test_calculate_raster_coordinates(
    geotransform, wkt_projection_string, geographic_coordinate, raster_coordinate
):
    wkt_string = read_file_contents(wkt_projection_string)
    proj_crs = CRS.from_string(wkt_string)
    transformer = process_grib.get_transformer(NAD83_CRS, proj_crs)
    padf_transform = Affine.from_gdal(*geotransform)
    longitude, latitude = geographic_coordinate
    expected_raster_coordinate = process_grib.calculate_raster_coordinate(
        longitude, latitude, padf_transform, transformer
    )
    assert expected_raster_coordinate == raster_coordinate
