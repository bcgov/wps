""" BDD tests for grib file processing """
import os
import logging
import json
from operator import itemgetter
from pytest_bdd import scenario, given, then, when
from pyproj import CRS
import app.weather_models.process_grib as process_grib

logger = logging.getLogger(__name__)


def read_file_contents(filename):
    """ Given a filename, return json """
    dirname = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dirname, filename), 'r') as file:
        return file.read()


@scenario(
    'test_grib_processing.feature',
    'Extract origin and pixel information',
    example_converters=dict(filename=str, origin=json.loads, pixels=json.loads))
def test_extract_origin_and_pixel_information():
    """ BDD Scenario. """


@given('a grib file: <filename>', target_fixture='grib_file')
def given_grib_file(filename):
    """ Open the dataset. """
    dirname = os.path.dirname(os.path.realpath(__file__))
    return dict(dataset=process_grib.open_grib(os.path.join(dirname, filename)))


@when('I extract the geometry')
def when_extract_geometry(grib_file):
    """ extract geometry """
    grib_file['geometry'] = process_grib.get_dataset_geometry(
        grib_file['dataset'])


@then('I expect <origin>')
def assert_origin(grib_file, origin):
    """ assert that origin matches expected """
    actual_origin = itemgetter(0, 3)(grib_file['geometry'])
    logger.warning('actual: %s ; expected %s', actual_origin, origin)
    # This fails when using gdal-2.2.3! Be sure to use a more recent version.
    assert origin == list(actual_origin)


@then('I expect <pixels>')
def assert_pixels(grib_file, pixels):
    """ assert that pixels match expected """
    actual_pixels = itemgetter(1, 5)(grib_file['geometry'])
    assert list(actual_pixels) == pixels


@scenario(
    'test_grib_processing.feature',
    'Extract the surrounding grid',
    example_converters=dict(filename=str, raster_coordinate=json.loads, points=json.loads, values=json.loads))
def test_surrounding_grid():
    """ BDD Scenario. """


@when('I get the surrounding grid for <raster_coordinate>')
def get_surrounding_grid(grib_file, raster_coordinate):
    """ get grid surrounding given coordinate """
    # Get the band with data.
    raster_band = grib_file['dataset'].GetRasterBand(1)
    x, y = raster_coordinate  # pylint: disable=invalid-name
    # Get the surrounding grid.
    surrounding_grid = process_grib.get_surrounding_grid(raster_band, x, y)
    grib_file['points'] = surrounding_grid[0]
    grib_file['values'] = surrounding_grid[1]


@then('I expect <points>')
def assert_points(grib_file, points):
    """ assert that expected points are found """
    actual_points = grib_file['points']
    expected_points = points
    assert actual_points == expected_points


@then('I expect <values>')
def assert_values(grib_file, values):
    """ assert values match """
    actual_values = grib_file['values']
    expected_values = values
    assert actual_values == expected_values


@scenario(
    'test_grib_processing.feature',
    'Calculate raster coordinates',
    example_converters=dict(geotransform=json.loads,
                            wkt_projection_string=read_file_contents,
                            geographic_coordinate=json.loads,
                            raster_coordinate=json.loads))
def test_calculate_raster_coordinates():
    """ BDD Scenario. """


@given('a GDAL <geotransform> and <wkt_projection_string>', target_fixture='data')
def given_geotransform_and_projection_string(geotransform, wkt_projection_string):
    """ return dict with geotransform and projection_string loaded from WKT file """
    return dict(geotransform=geotransform, wkt_projection_string=wkt_projection_string)


@when('I calculate the raster coordinate for <geographic_coordinate>')
def when_calculate_raster_coordinate(data, geographic_coordinate):
    """ calculate the raster coordinate """
    longitude, latitude = geographic_coordinate
    proj_crs = CRS.from_string(data['wkt_projection_string'])
    transformer = process_grib.get_transformer(process_grib.GEO_CRS, proj_crs)
    data['raster_coordinate'] = process_grib.calculate_raster_coordinate(
        longitude, latitude, data['geotransform'], transformer)


@then('I expect <raster_coordinate>')
def assert_raster_coordinates(data, raster_coordinate):
    """ assert that raster_coordinate matches expected value """
    assert list(data['raster_coordinate']) == raster_coordinate


@scenario(
    'test_grib_processing.feature',
    'Calculate geographic coordinates',
    example_converters=dict(
        geotransform=json.loads,
        wkt_projection_string=read_file_contents,
        raster_coordinate=json.loads,
        geographic_coordinate=json.loads))
def test_calculate_geographic_coordinates():
    """ BDD Scenario for testing calculation of geographic coordinates """


@when('I calculate the geographic coordinate for <raster_coordinate>')
def calculate_geographic_coordinate(data, raster_coordinate):
    """ calculate the geographic coordinate """
    proj_crs = CRS.from_string(data['wkt_projection_string'])
    transformer = process_grib.get_transformer(proj_crs, process_grib.GEO_CRS)
    data['geographic_coordinate'] = \
        process_grib.calculate_geographic_coordinate(
        raster_coordinate, data['geotransform'], transformer)


@then('I expect <geographic_coordinate>')
def assert_geographic_coordinate(data, geographic_coordinate):
    """ assert that geographic_coordinate matches the expected value """
    assert list(data['geographic_coordinate']) == geographic_coordinate
