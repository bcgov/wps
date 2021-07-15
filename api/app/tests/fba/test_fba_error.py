"""
Unit tests for fire behavour calculator.
"""
from datetime import date
from typing import Final
import logging
from pytest_bdd import scenario, given, then
from app import configure_logging
from app.utils.time import get_hour_20_from_date
from app.utils.fba_calculator import calculate_fire_behavour_advisory, FBACalculatorWeatherStation
from app.utils.redapp import FBPCalculateStatisticsCOM
import pytest


configure_logging()

logger = logging.getLogger(__name__)


class RelativeErrorException(Exception):
    """ Exception raised when it's mathematically impossible to calculate the relative error. """
    pass


def _str2float(value: str):
    if value == 'None':
        return None
    return float(value)


acceptable_margin_of_error: Final = 0.01


@pytest.mark.usefixtures('mock_jwt_decode')
@scenario('test_fba_error.feature', 'Fire Behaviour Calculation',
          example_converters=dict(elevation=float,
                                  latitude=float,
                                  longitude=float,
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
                                  red_app_error_margin=_str2float,
                                  r_h1_em=float,
                                  r_ros_em=float,
                                  r_hfi_em=float,
                                  r_cfb_em=float,
                                  s_h1_em=float,
                                  s_ros_em=float,
                                  s_hfi_em=float,
                                  s_cfb_em=float,
                                  spreadsheet_cfb=_str2float,
                                  spreadsheet_error_margin=_str2float,
                                  spreadsheet_hfi=_str2float,
                                  spreadsheet_ros=_str2float,
                                  spreadsheet_1hr=_str2float,
                                  time_of_interest=date.fromisoformat,
                                  wind_direction=float,
                                  wind_speed=float,
                                  note=str))
def test_fire_behaviour_calculator_scenario():
    """ BDD Scenario. """


@given("""<elevation>, <latitude>, <longitude>, <time_of_interest>, <wind_speed>, <wind_direction>, """
       """<percentage_conifer>, <percentage_dead_balsam_fir>, <grass_cure>, <crown_base_height>, """
       """<isi>, <bui>, <ffmc>, <dmc>, <dc>, <fuel_type>, <red_app_error_margin>""",
       target_fixture='result')
def given_input(elevation: float,  # pylint: disable=too-many-arguments, invalid-name
                latitude: float, longitude: float, time_of_interest: str,
                wind_speed: float, wind_direction: float,
                percentage_conifer: float, percentage_dead_balsam_fir: float, grass_cure: float,
                crown_base_height: float,
                isi: float, bui: float, ffmc: float, dmc: float, dc: float, fuel_type: str,
                red_app_error_margin: float):
    # get python result:
    python_input = FBACalculatorWeatherStation(elevation=elevation,
                                               fuel_type=fuel_type,
                                               time_of_interest=time_of_interest,
                                               percentage_conifer=percentage_conifer,
                                               percentage_dead_balsam_fir=percentage_dead_balsam_fir,
                                               grass_cure=grass_cure,
                                               crown_base_height=crown_base_height,
                                               lat=latitude,
                                               long=longitude,
                                               bui=bui,
                                               ffmc=ffmc,
                                               isi=isi,
                                               wind_speed=wind_speed)
    python_fba = calculate_fire_behavour_advisory(python_input)
    # get java result:
    if red_app_error_margin is None:
        java_fbp = None
    else:
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
        'java': java_fbp,
        'fuel_type': fuel_type
    }


def relative_error(metric: str, actual: float, expected: float, precision: int = 2):
    """ calculate the relative error between two values - default to precision of 2"""
    actual = round(actual, precision)
    expected = round(expected, precision)
    if actual == expected:
        return 0
    if expected == 0:
        raise RelativeErrorException(
            f'unable to calculate relative error for {metric}; actual:{actual};expected:{expected}')
    return abs((actual-expected)/expected)


def check_metric(metric: str,
                 fuel_type: str,
                 python_value: float,
                 comparison_value: float,
                 metric_error_margin: float, note: str = None):
    """ Check relative error of a metric """
    # logging with %s just became unreadable:
    # pylint: disable=logging-fstring-interpolation
    if comparison_value is None:
        logger.warning('Skipping %s! (%s) - note: %s', metric, comparison_value, note)
    else:
        assert python_value >= 0
        error = relative_error(f'{metric}', python_value, comparison_value)
        logger.info(
            f'{fuel_type}: Python {python_value}, {metric} {comparison_value} ; error: {error}')
        if error > acceptable_margin_of_error:
            logger.error('%s spreadsheet %s relative error greater than (%s)! (%s)',
                         fuel_type, metric, acceptable_margin_of_error, error)
        if metric_error_margin > 0.01:
            logger.warning('%s: The acceptable margin of error (%s) for %s is set too high',
                           fuel_type, metric_error_margin, metric)
        assert error < metric_error_margin, f'{fuel_type}:{metric}'


@then("ROS is within <s_ros_em> of <spreadsheet_ros> with <note>")
def then_spreadsheet_ros(result: dict, s_ros_em: float, spreadsheet_ros: float, note: str):
    """ check the relative error of the ros """
    check_metric('Spreadsheet ROS',
                 result['fuel_type'],
                 result['python'].ros,
                 spreadsheet_ros,
                 s_ros_em,
                 note)


@then("CFB is within <s_cfb_em> of <spreadsheet_cfb> with <note>")
def then_spreadsheet_cfb(result: dict, s_cfb_em: float, spreadsheet_cfb: float, note: str):
    """ check the relative error of the cfb """
    if spreadsheet_cfb is None or spreadsheet_cfb < 0:
        logger.warning('Skipping spreadsheet CFB! (%s) - note: %s', spreadsheet_cfb, note)
    else:
        actual = result['python'].cfb
        assert actual >= 0
        error = relative_error('Spreadsheet CFB', actual, spreadsheet_cfb, 1)
        fuel_type = result['fuel_type']
        logger.info('%s: Python CFB %s, Spreadsheet CFB %s ; error: %s',
                    fuel_type, actual, spreadsheet_cfb, error)
        if error > acceptable_margin_of_error:
            logger.error('%s spreadsheet CFB relative error greater than (%s)! (%s)',
                         fuel_type, acceptable_margin_of_error, error)
        assert error < s_cfb_em


@then("HFI is within <s_hfi_em> of <spreadsheet_hfi> with <note>")
def then_spreadsheet_hfi(result: dict, s_hfi_em: float, spreadsheet_hfi: float, note: str):
    """ check the relative error of the hfi """
    if spreadsheet_hfi is None:
        logger.warning('Skipping spreadsheet HFI! (%s) - note: %s', spreadsheet_hfi, note)
    else:
        actual = result['python'].hfi
        assert actual >= 0
        error = relative_error('Spreadsheet HFI', actual, spreadsheet_hfi)
        fuel_type = result['fuel_type']
        logger.info('%s: Python HFI %s, Spreadsheet HFI %s ; error: %s',
                    fuel_type, actual, spreadsheet_hfi, error)
        if error > acceptable_margin_of_error:
            logger.error('%s spreadsheet HFI relative error greater than (%s)! (%s)',
                         fuel_type, acceptable_margin_of_error, error)
        assert error < s_hfi_em


@then("1 HR Size is within <s_h1_em> of <spreadsheet_1hr> with <note>")
def then_spreadsheet_1hr(result: dict, s_h1_em: float, spreadsheet_1hr: float, note: str):
    """ check the relative error of the 1 HR fire size"""
    check_metric('Spreadsheet 1 HR Size',
                 result['fuel_type'],
                 result['python'].sixty_minute_fire_size,
                 spreadsheet_1hr,
                 s_h1_em,
                 note)


@then("ROS is within <r_ros_em> of REDapp ROS")
def then_red_app_ros(result: dict, r_ros_em: float):
    """ check the relative error of ROS """
    fuel_type = result['fuel_type']
    if r_ros_em is None:
        logger.info('%s: skipping ROS for redapp', fuel_type)
    else:
        actual = result['python'].ros
        assert actual >= 0
        expected = result['java'].ros_t
        error = relative_error('RedAPP ROS', actual, expected)
        logger.info('%s: Python ROS %s, REDapp ROS %s ; error: %s', fuel_type, actual, expected, error)
        if error > acceptable_margin_of_error:
            logger.error('%s REDapp ROS relative error greater than (%s)! (%s)',
                         fuel_type, acceptable_margin_of_error, error)
        assert error < r_ros_em


@then("CFB is within <r_cfb_em> of REDapp CFB")
def then_red_app_cfb(result: dict, r_cfb_em: float):
    """ check the relative error fo the CFB """
    fuel_type = result['fuel_type']
    if r_cfb_em is None:
        logger.info('%s: skipping ROS for redapp', fuel_type)
    else:
        # python gives CFB as 0-1
        actual = result['python'].cfb*100
        assert actual >= 0
        # redapp gives CFB as 0-100
        expected = result['java'].cfb
        logger.info('%s: CFB: python: %s ; REDapp: %s', fuel_type, actual, expected)
        error = relative_error('RedAPP CFB', actual, expected)
        logger.info('%s: Python CFB %s, REDapp CFB %s ; error: %s', fuel_type, actual, expected, error)
        if error > acceptable_margin_of_error:
            logger.error('%s REDapp CFB relative error greater than (%s)! (%s)',
                         fuel_type, acceptable_margin_of_error, error)
        assert error < r_cfb_em


@then("HFI is within <r_hfi_em> of REDapp HFI")
def then_red_app_hfi(result: dict, r_hfi_em: float):
    """ check the relative error fo the CFB """
    fuel_type = result['fuel_type']
    if r_hfi_em is None:
        logger.info('%s: skipping ROS for redapp', fuel_type)
    else:
        actual = result['python'].hfi
        assert actual >= 0
        expected = result['java'].hfi
        error = relative_error('RedAPP HFI', actual, expected)
        logger.info('%s: Python HFI %s, REDapp HFI %s ; error: %s', fuel_type, actual, expected, error)
        if error > acceptable_margin_of_error:
            logger.error('%s REDapp HFI relative error greater than (%s)! (%s)',
                         fuel_type, acceptable_margin_of_error, error)
        assert error < r_hfi_em


@then("1 HR Size is within <r_h1_em> of REDapp 1 HR Size")
def then_red_app_1hr(result: dict, r_h1_em: float):
    check_metric('REDapp 1 HR Size',
                 result['fuel_type'],
                 result['python'].sixty_minute_fire_size,
                 result['java'].area,
                 r_h1_em)


@then("<spreadsheet_error_margin> <red_app_error_margin>")
def then_get_rid_of_this(spreadsheet_error_margin, red_app_error_margin):
    pass
