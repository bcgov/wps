""" BDD tests for grib file processing """
import os
import logging
import json
from operator import itemgetter
from affine import Affine
from pytest_bdd import scenario, given, then, when, parsers
from pyproj import CRS
from app.geospatial import NAD83_CRS
import app.weather_models.process_grib as process_grib

logger = logging.getLogger(__name__)


def read_file_contents(filename):
    """ Given a filename, return json """
    dirname = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dirname, filename), 'r') as file:
        return file.read()


@scenario(
    'test_grib_processing.feature',
    'Extract origin and pixel information')
def test_extract_origin_and_pixel_information():
    """ BDD Scenario. """


@given(parsers.parse('a grib file: {filename}'), target_fixture='grib_file', converters={'filename': str})
def given_grib_file(filename):
    """ Open the dataset. """
    dirname = os.path.dirname(os.path.realpath(__file__))
    full_path = os.path.join(dirname, filename)
    return dict(dataset=process_grib.open_grib(full_path), filename=full_path)


@when('I extract the geometry')
def when_extract_geometry(grib_file):
    """ extract geometry """
    grib_file['geometry'] = process_grib.get_dataset_geometry(
        grib_file['filename'])


@then(parsers.parse('I expect origin: {origin}'), converters={'origin': json.loads})
def assert_origin(grib_file, origin):
    """ assert that origin matches expected """
    actual_origin = itemgetter(0, 3)(grib_file['geometry'].to_gdal())
    logger.warning('actual: %s ; expected %s', actual_origin, origin)
    # This fails when using gdal-2.2.3! Be sure to use a more recent version.
    assert origin == list(actual_origin)


@then(parsers.parse('I expect pixels: {pixels}'), converters={'pixels': json.loads})
def assert_pixels(grib_file, pixels):
    """ assert that pixels match expected """
    actual_pixels = itemgetter(1, 5)(grib_file['geometry'].to_gdal())
    assert list(actual_pixels) == pixels


@scenario(
    'test_grib_processing.feature',
    'Extract the surrounding grid')
def test_surrounding_grid():
    """ BDD Scenario. """


@when(parsers.parse('I get the surrounding grid for {raster_coordinate}'), converters={'raster_coordinate': json.loads})
def get_surrounding_grid(grib_file, raster_coordinate):
    """ get grid surrounding given coordinate """
    # Get the band with data.
    raster_band = grib_file['dataset'].GetRasterBand(1)
    x, y = raster_coordinate
    # Get the surrounding grid.
    surrounding_grid = process_grib.get_surrounding_grid(raster_band, x, y)
    grib_file['points'] = surrounding_grid[0]
    grib_file['values'] = surrounding_grid[1]


@then(parsers.parse('I expect points: {points}'), converters={'points': json.loads})
def assert_points(grib_file, points):
    """ assert that expected points are found """
    actual_points = grib_file['points']
    expected_points = points
    assert actual_points == expected_points


@then(parsers.parse('I expect values: {values}'), converters={'values': json.loads})
def assert_values(grib_file, values):
    """ assert values match """
    actual_values = grib_file['values']
    expected_values = values
    assert actual_values == expected_values


@scenario(
    'test_grib_processing.feature',
    'Calculate raster coordinates')
def test_calculate_raster_coordinates():
    """ BDD Scenario. """


@given(parsers.parse('a GDAL {geotransform} and {wkt_projection_string}'), target_fixture='data', converters={'geotransform': json.loads, 'wkt_projection_string': read_file_contents})
def given_geotransform_and_projection_string(geotransform, wkt_projection_string):
    """ return dict with geotransform and projection_string loaded from WKT file """
    return dict(geotransform=geotransform, wkt_projection_string=wkt_projection_string)


@when(parsers.parse('I calculate the raster coordinate for {geographic_coordinate}'), converters={'geographic_coordinate': json.loads})
def when_calculate_raster_coordinate(data, geographic_coordinate):
    """ calculate the raster coordinate """
    longitude, latitude = geographic_coordinate
    proj_crs = CRS.from_string(data['wkt_projection_string'])
    transformer = process_grib.get_transformer(NAD83_CRS, proj_crs)
    padf_transform = Affine.from_gdal(*data['geotransform'])
    data['raster_coordinate'] = process_grib.calculate_raster_coordinate(
        longitude, latitude, padf_transform, transformer)


@then(parsers.parse('I expect raster coordinates: {raster_coordinate}'), converters={'raster_coordinate': json.loads})
def assert_raster_coordinates(data, raster_coordinate):
    """ assert that raster_coordinate matches expected value """
    assert list(data['raster_coordinate']) == raster_coordinate


@scenario(
    'test_grib_processing.feature',
    'Calculate geographic coordinates')
def test_calculate_geographic_coordinates():
    """ BDD Scenario for testing calculation of geographic coordinates """


@when(parsers.parse('I calculate the geographic coordinate for {raster_coordinate}'), converters={'raster_coordinate': json.loads})
def calculate_geographic_coordinate(data, raster_coordinate):
    """ calculate the geographic coordinate """
    proj_crs = CRS.from_string(data['wkt_projection_string'])
    transformer = process_grib.get_transformer(proj_crs, NAD83_CRS)
    padf_transform = Affine.from_gdal(*data['geotransform'])
    data['geographic_coordinate'] = \
        process_grib.calculate_geographic_coordinate(
        raster_coordinate, padf_transform, transformer)


@then(parsers.parse('I expect the geographic_coordinate {geographic_coordinate}'), converters={'geographic_coordinate': json.loads})
def assert_geographic_coordinate(data, geographic_coordinate):
    """ assert that geographic_coordinate matches the expected value """
    assert list(data['geographic_coordinate']) == geographic_coordinate


@scenario('test_grib_processing.feature', 'Calculate wind speed and direction from U,V components')
def test_calculate_wind_speed_direction():
    """ BDD Scenario for testing calculation of wind speed and wind direction from U,V components """


@given(parsers.parse('a U value {u_float} and V value {v_float}'), target_fixture='data', converters={'u_float': float, 'v_float': float})
def given_u_and_v_values(u_float, v_float):
    return dict(u_float=u_float, v_float=v_float)


@when(parsers.parse('I calculate the wind speed'))
def when_calculate_wind_speed(data):
    """ calculate the wind speed from U,V components """
    data['actual_wind_speed'] = process_grib.calculate_wind_speed_from_u_v(data['u_float'], data['v_float'])


@when(parsers.parse('I calculate the wind direction'))
def when_calculate_wind_direction(data):
    """ calculate the wind direction from U,V components """
    data['actual_wind_dir'] = process_grib.calculate_wind_dir_from_u_v(data['u_float'], data['v_float'])


@then(parsers.parse('I expect a calculated wind speed of {expected_wind_speed}'), converters={'expected_wind_speed': json.loads})
def assert_wind_speed(data, expected_wind_speed):
    """ assert that calculated wind speed matches the expected value """
    assert round(data['actual_wind_speed'], 2) == expected_wind_speed


@then(parsers.parse('I expect a calculated wind direction of {expected_wind_dir}'), converters={'expected_wind_dir': json.loads})
def assert_wind_direction(data, expected_wind_dir):
    """ assert that calculated wind direction matches the expected value """
    assert round(data['actual_wind_dir'], 0) == expected_wind_dir
