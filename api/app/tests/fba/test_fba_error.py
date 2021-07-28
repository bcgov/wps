"""
Unit tests for fire behavour calculator.
"""
from datetime import date
from typing import Final
import logging
from pytest_bdd import scenario, given, then
from app import configure_logging
from app.utils.time import get_hour_20_from_date
from app.utils.fba_calculator import calculate_fire_behaviour_advisory, FBACalculatorWeatherStation
from app.utils.redapp import FBPCalculateStatisticsCOM
import pytest


configure_logging()

logger = logging.getLogger(__name__)

acceptable_margin_of_error: Final = 0.01


class RelativeErrorException(Exception):
    """ Exception raised when it's mathematically impossible to calculate the relative error. """


def _str2float(value: str):
    if value == 'None':
        return None
    return float(value)


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
                 test_scenario: str,
                 fuel_type: str,
                 python_value: float,
                 comparison_value: float,
                 metric_error_margin: float,
                 note: str):
    """ Check relative error of a metric """
    # logging with %s became unreadable:
    # pylint: disable=logging-fstring-interpolation
    if comparison_value is None:
        logger.warning('Skipping %s! (%s) - note: %s', metric, comparison_value, note)
    elif comparison_value < 0:
        logger.warning('Skipping %s! (%s) - note: %s', metric, comparison_value, note)
    else:
        assert python_value >= 0
        error = relative_error(f'{metric}', python_value, comparison_value)
        logger.info(
            f'{fuel_type}: Python {python_value}, {metric} {comparison_value} ; error: {error}')
        if error > acceptable_margin_of_error:
            logger.error('%s %s relative error %s > %s! (actual: %s, expected: %s)',
                         fuel_type, metric, error, acceptable_margin_of_error, python_value, comparison_value)
        if metric_error_margin > 0.01:
            logger.warning('%s: The acceptable margin of error (%s) for %s is set too high',
                           fuel_type, metric_error_margin, metric)
        if error > metric_error_margin:
            absolute_error = abs(python_value - comparison_value)
            if absolute_error < 0.01:
                logger.info('no big deal, the absolute difference (%s) is tiny!', absolute_error)
            else:
                assert error < metric_error_margin, f'{test_scenario}:{fuel_type}:{metric} {note}'


@pytest.mark.usefixtures('mock_jwt_decode')
@scenario('test_fba_error.feature', 'Fire Behaviour Calculation - vs. REDapp',
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
                                  one_hr_em=float,
                                  ros_em=float,
                                  hfi_em=float,
                                  cfb_em=float,
                                  time_of_interest=date.fromisoformat,
                                  wind_direction=float,
                                  wind_speed=float,
                                  note=str))
def test_fire_behaviour_calculator_scenario():
    """ BDD Scenario. """


@given("""<elevation>, <latitude>, <longitude>, <time_of_interest>, <wind_speed>, <wind_direction>, """
       """<percentage_conifer>, <percentage_dead_balsam_fir>, <grass_cure>, <crown_base_height>, """
       """<isi>, <bui>, <ffmc>, <dmc>, <dc>, <fuel_type>""",
       target_fixture='result')
def given_red_app_input(elevation: float,  # pylint: disable=too-many-arguments, invalid-name
                        latitude: float, longitude: float, time_of_interest: str,
                        wind_speed: float, wind_direction: float,
                        percentage_conifer: float, percentage_dead_balsam_fir: float, grass_cure: float,
                        crown_base_height: float,
                        isi: float, bui: float, ffmc: float, dmc: float, dc: float, fuel_type: str):
    """ Take input and calculate actual and expected results """
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
                                               wind_speed=wind_speed,
                                               wind_direction=wind_direction,
                                               temperature=20.0,  # temporary fix so tests don't break
                                               relative_humidity=20.0,
                                               precipitation=2.0,
                                               status='Forecasted',
                                               prev_day_daily_ffmc=90.0,
                                               last_observed_morning_rh_values={
                                                   7.0: 61.0, 8.0: 54.0, 9.0: 43.0, 10.0: 38.0,
                                                   11.0: 34.0, 12.0: 23.0})
    python_fba = calculate_fire_behaviour_advisory(python_input)
    # get REDapp result from java:
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

    # NOTE: REDapp has a ros_eq and a ros_t ;
    # assumptions:
    # ros_eq == ROScalc
    # ros_t  == ROStcalc
    expected = {
        'ros': java_fbp.ros_eq,
        'ros_t': java_fbp.ros_t,
        'cfb': java_fbp.cfb/100.0,  # CFFDRS gives cfb as a fraction
        'hfi': java_fbp.hfi,
        'area': java_fbp.area
    }

    return {
        'python': python_fba,
        'expected': expected,
        'fuel_type': fuel_type,
        'scenario': 'REDapp'
    }


@then("ROS is within <ros_em> (<note>)")
def then_ros(result: dict, ros_em: float, note: str):
    """ check the relative error of the ros """
    check_metric('ROS',
                 result['scenario'],
                 result['fuel_type'],
                 result['python'].ros,
                 result['expected']['ros'],
                 ros_em,
                 note)


@then("ROS_t is within range (<note>)")
def then_ros_t(result: dict, note: str):
    """ check the relative error of the ros """
    check_metric('ROS_t',
                 result['scenario'],
                 result['fuel_type'],
                 result['python'].ros_t,
                 result['expected']['ros_t'],
                 acceptable_margin_of_error,
                 note)


@then("CFB is within <cfb_em> (<note>)")
def then_cfb(result: dict, cfb_em: float, note: str):
    """ check the relative error of the cfb """
    check_metric('CFB',
                 result['scenario'],
                 result['fuel_type'],
                 result['python'].cfb,
                 result['expected']['cfb'],
                 cfb_em,
                 note)


@then("HFI is within <hfi_em> (<note>)")
def then_hfi(result: dict, hfi_em: float, note: str):
    """ check the relative error of the hfi """
    check_metric('HFI',
                 result['scenario'],
                 result['fuel_type'],
                 result['python'].hfi,
                 result['expected']['hfi'],
                 hfi_em,
                 note)


@then("1 HR Size is within <one_hr_em> (<note>)")
def then_one_hr(result: dict, one_hr_em: float, note: str):
    """ check the relative error of the a hour fire size"""
    check_metric('1 HR Size',
                 result['scenario'],
                 result['fuel_type'],
                 result['python'].sixty_minute_fire_size,
                 result['expected']['area'],
                 one_hr_em,
                 note)


@pytest.mark.usefixtures('mock_jwt_decode')
@scenario('test_fba_error.feature', 'Fire Behaviour Calculation - vs. Spreadsheet',
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
                                  ros_em=float,
                                  hfi_em=float,
                                  cfb_em=float,
                                  cfb=_str2float,
                                  hfi=_str2float,
                                  ros=_str2float,
                                  time_of_interest=date.fromisoformat,
                                  wind_direction=float,
                                  wind_speed=float,
                                  note=str))
def test_fire_behaviour_calculator_spreadsheet_scenario():
    """ BDD Scenario. """


@given("""<elevation>, <latitude>, <longitude>, <time_of_interest>, <wind_speed>, <wind_direction>, """
       """<percentage_conifer>, <percentage_dead_balsam_fir>, <grass_cure>, <crown_base_height>, <isi>, """
       """<bui>, <ffmc>, <dmc>, <dc>, <fuel_type>, <ros>, <hfi>, <cfb>""",
       target_fixture='result')
def given_spreadsheet_input(elevation: float,  # pylint: disable=too-many-arguments, invalid-name
                            latitude: float, longitude: float, time_of_interest: str,
                            wind_speed: float, wind_direction: float,
                            percentage_conifer: float, percentage_dead_balsam_fir: float, grass_cure: float,
                            crown_base_height: float,
                            isi: float, bui: float, ffmc: float, dmc: float, dc: float, fuel_type: str,
                            ros: float, hfi: float, cfb: float):
    """ Take input and calculate actual and expected results """
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
                                               wind_speed=wind_speed,
                                               wind_direction=wind_direction,
                                               temperature=20.0,  # temporary fix so tests don't break
                                               relative_humidity=20.0,
                                               precipitation=2.0,
                                               status='Forecasted',
                                               prev_day_daily_ffmc=90.0,
                                               last_observed_morning_rh_values={
                                                   7.0: 61.0, 8.0: 54.0, 9.0: 43.0, 10.0: 38.0,
                                                   11.0: 34.0, 12.0: 23.0})
    python_fba = calculate_fire_behaviour_advisory(python_input)

    expected = {
        'ros': ros,
        'cfb': cfb,
        'hfi': hfi,
        'area': None
    }

    return {
        'python': python_fba,
        'expected': expected,
        'fuel_type': fuel_type,
        'scenario': 'Spreadsheet'
    }
