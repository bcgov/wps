""" BDD tests for processing file from env. Canada. """
import logging
from pytest_bdd import scenario, given, then, parsers
from app.weather_models.env_canada import parse_env_canada_filename
from app.weather_models.process_grib import ModelRunInfo

logger = logging.getLogger(__name__)


@scenario('test_parse_env_canada_filename.feature', 'Parse a grib filename')
def test_parse():
    """ BDD Scenario. """


@given(parsers.parse('I have a grib file {filename}'), target_fixture='parsed_file', converters={'filename': str})
def given_grib_file(filename: str) -> ModelRunInfo:
    """ Parse filename.
    """
    return parse_env_canada_filename(filename)


@then(parsers.parse('The projection is {projection}'), converters={'projection': str})
def assert_status_code(parsed_file: ModelRunInfo, projection: str):
    """ Assert that we recieve the expected status code """
    assert parsed_file.projection == projection


@then(parsers.parse('The variable_name is {variable_name}'), converters={'variable_name': str})
def assert_variable_name(parsed_file: ModelRunInfo, variable_name: str):
    """ Assert that we recieve the expected status code """
    assert parsed_file.variable_name == variable_name
