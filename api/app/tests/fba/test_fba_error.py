"""
Unit tests for fire behavour calculator.
"""
from datetime import date
import logging
from pytest_bdd import scenario, given, then
from app import configure_logging
from app.utils.time import get_hour_20_from_date
from app.utils.fba_calculator import calculate_fire_behavour_advisory, FBACalculatorWeatherStation
from app.utils.redapp import FBPCalculateStatisticsCOM
import pytest


configure_logging()

logger = logging.getLogger(__name__)


def _str2float(value: str):
    if value == 'None':
        return None
    return float(value)


@pytest.mark.usefixtures('mock_jwt_decode')
@scenario('test_fba_error.feature', 'Fire Behaviour Calculation',
          example_converters=dict(elevation=float,
                                  latitude=float,
                                  longitude=float,
                                  time_of_interest=date.fromisoformat,
                                  wind_speed=float,
                                  wind_direction=float,
                                  percentage_conifer=_str2float,
                                  percentage_dead_balsam_fir=_str2float,
                                  crown_base_height=_str2float,
                                  grass_cure=_str2float,
                                  isi=float,
                                  bui=float,
                                  ffmc=float,
                                  dmc=float,
                                  dc=float,
                                  fuel_type=str,
                                  red_app_error_margin=float,
                                  spreadsheet_error_margin=float,
                                  spreadsheet_ros=float,
                                  spreadsheet_hfi=float,
                                  spreadsheet_cfb=float))
def test_fire_behaviour_calculator_scenario():
    """ BDD Scenario. """


@given("""<elevation>, <latitude>, <longitude>, <time_of_interest>, <wind_speed>, <wind_direction>, """
       """<percentage_conifer>, <percentage_dead_balsam_fir>, <grass_cure>, <crown_base_height>, """
       """<isi>, <bui>, <ffmc>, <dmc>, <dc>, <fuel_type>""", target_fixture='result')
def given_input(elevation: float,  # pylint: disable=too-many-arguments, invalid-name
                latitude: float, longitude: float, time_of_interest: str,
                wind_speed: float, wind_direction: float,
                percentage_conifer: float, percentage_dead_balsam_fir: float, grass_cure: float,
                crown_base_height: float,
                isi: float, bui: float, ffmc: float, dmc: float, dc: float, fuel_type: str):
    # get python result:
    python_input = FBACalculatorWeatherStation(elevation=elevation,
                                               fuel_type=fuel_type,
                                               time_of_interest=time_of_interest,
                                               percentage_conifer=percentage_conifer,
                                               percentage_dead_balsam_fir=None,
                                               grass_cure=grass_cure,
                                               crown_base_height=crown_base_height,
                                               lat=latitude,
                                               long=longitude,
                                               bui=bui,
                                               ffmc=ffmc,
                                               isi=isi,
                                               wind_speed=wind_speed,
                                               temperature=20.0,  # temporary fix so tests don't break
                                               relative_humidity=20.0,
                                               precipitation=2.0,
                                               status='Forecasted')
    python_fba = calculate_fire_behavour_advisory(python_input)
    # get java result:
    java_fbp = FBPCalculateStatisticsCOM(elevation=elevation,
                                         latitude=latitude,
                                         longitude=longitude,
                                         time_of_interest=get_hour_20_from_date(time_of_interest),
                                         fuel_type=fuel_type,
                                         ffmc=ffmc,
                                         dmc=dmc,
                                         dc=dc,
                                         bui=bui,
                                         wind_speed=wind_speed,
                                         wind_direction=wind_direction,
                                         percentage_conifer=percentage_conifer,
                                         percentage_dead_balsam_fir=percentage_dead_balsam_fir,
                                         grass_cure=grass_cure,
                                         crown_base_height=crown_base_height)

    return {
        'python': python_fba,
        'java': java_fbp
    }


def relative_error(actual: float, expected: float, precision: int = 2):
    """ calculate the relative error between two values - default to precision of 2"""
    actual = round(actual, precision)
    expected = round(expected, precision)
    return abs((actual-expected)/expected)


@then("ROS is within <spreadsheet_error_margin> of <spreadsheet_ros>")
def then_spreadsheet_ros(result: dict, spreadsheet_error_margin: float, spreadsheet_ros: float):
    """ check the relative error of the ros """
    actual = result['python'].ros
    error = relative_error(actual, spreadsheet_ros)
    logger.info('Python ROS %s, Spreadsheet ROS %s ; error: %s', actual, spreadsheet_ros, error)
    assert error < spreadsheet_error_margin


@then("CFB is within <spreadsheet_error_margin> of <spreadsheet_cfb>")
def then_spreadsheet_cfb(result: dict, spreadsheet_error_margin: float, spreadsheet_cfb: float):
    """ check the relative error of the cfb """
    actual = result['python'].cfb
    error = relative_error(actual, spreadsheet_cfb, 1)
    logger.info('Python CFB %s, Spreadsheet CFB %s ; error: %s', actual, spreadsheet_cfb, error)
    assert error < spreadsheet_error_margin


@then("HFI is within <spreadsheet_error_margin> of <spreadsheet_hfi>")
def then_spreadsheet_hfi(result: dict, spreadsheet_error_margin: float, spreadsheet_hfi: float):
    """ check the relative error of the hfi """
    actual = result['python'].hfi
    error = relative_error(actual, spreadsheet_hfi)
    logger.info('Python HFI %s, Spreadsheet HFI %s ; error: %s', actual, spreadsheet_hfi, error)
    assert error < spreadsheet_error_margin


@then("ROS is within <red_app_error_margin> of REDapp ROS")
def then_red_app_ros(result: dict, red_app_error_margin: float):
    """ check the relative error of ROS """
    actual = result['python'].ros
    expected = result['java'].ros_t
    error = relative_error(actual, expected)
    logger.info('Python ROS %s, REDapp ROS %s ; error: %s', actual, expected, error)
    assert error < red_app_error_margin


@then("CFB is within <red_app_error_margin> of REDapp CFB")
def then_red_app_cfb(result: dict, red_app_error_margin: float):
    """ check the relative error fo the CFB """
    # python gives CFB as 0-1
    actual = result['python'].cfb*100
    # redapp gives CFB as 0-100
    expected = result['java'].cfb
    error = relative_error(actual, expected)
    logger.info('Python CFB %s, REDapp CFB %s ; error: %s', actual, expected, error)
    assert error < red_app_error_margin


@then("HFI is within <red_app_error_margin> of REDapp HFI")
def then_red_app_hfi(result: dict, red_app_error_margin: float):
    """ check the relative error fo the CFB """
    actual = result['python'].hfi
    expected = result['java'].hfi
    error = relative_error(actual, expected)
    logger.info('Python HFI %s, REDapp HFI %s ; error: %s', actual, expected, error)
    assert error < red_app_error_margin
