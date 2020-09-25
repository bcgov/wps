""" BDD tests for processing file from env. Canada. """
import logging
from pytest_bdd import scenario, given, then
from app.models.env_canada import parse_env_canada_filename

LOGGER = logging.getLogger(__name__)


@scenario('test_parse_env_canada_filename.feature', 'Parse a grib filename',
          example_converters=dict(filename=str, projection=str))
def test_parse():
    """ BDD Scenario. """


@given('I have a grib file <filename>')
def parsed_file(filename):
    """ Make /hourlies/ request using mocked out ClientSession.
    """
    return parse_env_canada_filename(filename)


@then('The projection is <projection>')
def assert_status_code(parsed_file, projection):  # pylint: disable=redefined-outer-name
    """ Assert that we recieve the expected status code """
    assert parsed_file.projection == projection


@then('The variable_name is <variable_name>')
def assert_variable_name(parsed_file, variable_name):  # pylint: disable=redefined-outer-name
    """ Assert that we recieve the expected status code """
    assert parsed_file.variable_name == variable_name
