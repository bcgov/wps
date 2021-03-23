""" Test the bounding box logic.
"""
import os
import gdal
from pyproj import CRS
from pytest_bdd import scenario, given, then
from app.weather_models.process_grib import GEO_CRS, get_transformer
from app.c_haines.c_haines_index import BoundingBoxChecker


@scenario(
    'test_bounding_box.feature',
    'Check bounding box',
    example_converters=dict(
        grib_file=str, x_coordinate=int, y_coordinate=int, is_inside=lambda a: a.lower() == 'true'))
def test_extract_origin_and_pixel_information():
    """ BDD Scenario. """


@given('a <grib_file>', target_fixture='grib_info')
def given_a_grib_file(grib_file: str):
    """ Load up grib file and extract info. """
    dirname = os.path.dirname(os.path.realpath(__file__))
    dataset = gdal.Open(os.path.join(dirname, grib_file), gdal.GA_ReadOnly)
    crs = CRS.from_string(dataset.GetProjection())
    return {
        'padf_transform': dataset.GetGeoTransform(),
        'raster_to_geo_transformer': get_transformer(crs, GEO_CRS)
    }


@then('We expect the coordinate <x_coordinate> <y_coordinate> to be <is_inside>')
def with_temperature_and_dewpoint_values(
        x_coordinate: int,
        y_coordinate: int,
        is_inside: bool,
        grib_info: dict):
    """ Using the bounding box checker to validate if raster coordinate is inside or outside the
    bounding box. """
    bound_box_checker = BoundingBoxChecker(
        grib_info['padf_transform'], grib_info['raster_to_geo_transformer'])
    assert bound_box_checker.is_inside(x_coordinate, y_coordinate) == is_inside
