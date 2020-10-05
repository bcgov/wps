""" BDD tests for grib file processing """
import os
import logging
from pytest_bdd import scenario, given, then, when
import app.models.process_grib as process_grib

logger = logging.getLogger(__name__)


@scenario('test_grib_processing.feature', 'Extract origin and pixel information')
def test_extract_origin_and_pixel_information():
    """ BDD Scenario. """


@given('a grib file: <filename>')
def given_grib_file(filename):
    """ Open the dataset. """
    dirname = os.path.dirname(os.path.realpath(__file__))
    return dict(dataset=process_grib.open_grib(os.path.join(dirname, filename)))


@when('I extract the geometry')
def when_extract_geometry(given_grib_file):  # pylint: disable=redefined-outer-name
    """ extract geometry """
    given_grib_file['geometry'] = process_grib.get_dataset_geometry(
        given_grib_file['dataset'])


@then('I expect <origin>')
def assert_origin(given_grib_file, origin):  # pylint: disable=redefined-outer-name
    """ assert that origin matches expected """
    actual_origin = given_grib_file['geometry'][0]
    expected_origin = eval(origin)  # pylint: disable=eval-used
    logger.warning('actual: %s ; expected %s', actual_origin, expected_origin)
    # This fails when using gdal-2.2.3! Be sure to use a more recent version.
    assert expected_origin == actual_origin


@then('I expect <pixels>')
def assert_pixels(given_grib_file, pixels):  # pylint: disable=redefined-outer-name
    """ assert that pixels match expected """
    actual_pixels = given_grib_file['geometry'][1]
    expected_pixels = eval(pixels)  # pylint: disable=eval-used
    assert actual_pixels == expected_pixels


@scenario('test_grib_processing.feature', 'Extract the surrounding grid')
def test_surrounding_grid():
    """ BDD Scenario. """


@given('a <raster_coordinate>')
def given_raster_coordinate(raster_coordinate):
    """ parse coordinate string into array """
    return eval(raster_coordinate)  # pylint: disable=eval-used


@when('I get the surrounding grid')
def get_surrounding_grid(given_grib_file, given_raster_coordinate):  # pylint: disable=redefined-outer-name
    """ git grid surrounding given coordinate """
    # Get the band with data.
    raster_band = given_grib_file['dataset'].GetRasterBand(1)
    x, y = given_raster_coordinate  # pylint: disable=invalid-name
    # Get the surrounding grid.
    surrounding_grid = process_grib.get_surrounding_grid(raster_band, x, y)
    given_grib_file['points'] = surrounding_grid[0]
    given_grib_file['values'] = surrounding_grid[1]


@then('I expect <points>')
def assert_points(given_grib_file, points):  # pylint: disable=redefined-outer-name
    """ assert that expected points are found """
    actual_points = given_grib_file['points']
    expected_points = eval(points)  # pylint: disable=eval-used
    assert actual_points == expected_points


@then('I expect <values>')
def assert_values(given_grib_file, values):  # pylint: disable=redefined-outer-name
    """ assert values match """
    actual_values = given_grib_file['values']
    expected_values = eval(values)  # pylint: disable=eval-used
    assert actual_values == expected_values


@scenario('test_grib_processing.feature', 'Calculate raster coordinates')
def test_calculate_raster_coordinates():
    """ BDD Scenario. """


@given('an <origin> and <pixels>')
def given_origin_and_pixels(origin, pixels):
    """ return origin and pixels """
    return dict(origin=eval(origin), pixels=eval(pixels))  # pylint: disable=eval-used


@given('a geographic coordinate <geographic_coordinate>')
def given_geographic_coordinate(geographic_coordinate):
    """ parse coordinate """
    return eval(geographic_coordinate)  # pylint: disable=eval-used


@when('I calculate the raster coordinate')
def when_calculate_raster_coordinate(given_origin_and_pixels, given_geographic_coordinate):  # pylint: disable=redefined-outer-name
    """ calculate raster coordinates """
    longitude, latitude = given_geographic_coordinate
    origin = given_origin_and_pixels['origin']
    pixels = given_origin_and_pixels['pixels']
    given_origin_and_pixels['raster_coordinate'] = process_grib.calculate_raster_coordinate(
        longitude, latitude, origin, pixels)


@then('I expect <raster_coordinate>')
def assert_raster_coordinates(given_origin_and_pixels, raster_coordinate):  # pylint: disable=redefined-outer-name
    """ assert expected coordinates """
    assert given_origin_and_pixels['raster_coordinate'] == eval(  # pylint: disable=eval-used
        raster_coordinate)


@scenario('test_grib_processing.feature', 'Calculate geographic coordinates')
def test_calculate_geographic_coordinates():
    """ BDD Scenario for testing calculation of geographic coordinates """


@when('I calculate the geographic coordinate')
def calculate_geographic_coordinate(given_origin_and_pixels, given_raster_coordinate):  # pylint: disable=redefined-outer-name
    """ calculate geographic coordinate """
    origin = given_origin_and_pixels['origin']
    pixels = given_origin_and_pixels['pixels']
    given_origin_and_pixels['geographic_coordinate'] = process_grib.calculate_geographic_coordinate(
        given_raster_coordinate, origin, pixels)


@then('I expect <geographic_coordinate>')
def assert_geographic_coordinate(given_origin_and_pixels, geographic_coordinate):  # pylint: disable=redefined-outer-name
    """ assert expected geographic coordinate """
    expected_coordinate = eval(geographic_coordinate)  # pylint: disable=eval-used
    assert given_origin_and_pixels['geographic_coordinate'] == expected_coordinate
