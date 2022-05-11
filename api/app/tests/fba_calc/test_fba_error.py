"""
Unit tests for fire behavour calculator.
"""
from datetime import date
import logging
from pytest_bdd import scenario, given, then, parsers
from app import configure_logging
from app.schemas.fba_calc import FuelTypeEnum
from app.utils.time import get_hour_20_from_date
from app.fire_behaviour.advisory import calculate_fire_behaviour_advisory, FBACalculatorWeatherStation
from app.utils.redapp import FBPCalculateStatisticsCOM
from app.tests.common import str2float
from app.tests.fba_calc import (check_metric, acceptable_margin_of_error,
                                fire_size_acceptable_margin_of_error)
import pytest


configure_logging()

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures('mock_jwt_decode')
@scenario('test_fba_error.feature', 'Fire Behaviour Calculation - vs. REDapp')
def test_fire_behaviour_calculator_scenario():
    """ BDD Scenario. """


@given(
    parsers.parse("""REDapp input {elevation}, {latitude}, {longitude}, {time_of_interest}, {wind_speed}, {wind_direction}, """
                  """{percentage_conifer}, {percentage_dead_balsam_fir}, {grass_cure}, {crown_base_height}, """
                  """{isi}, {bui}, {ffmc}, {dmc}, {dc}, {fuel_type}"""),
    converters=dict(elevation=float,
                    latitude=float,
                    longitude=float,
                    time_of_interest=date.fromisoformat,
                    wind_speed=float,
                    wind_direction=str2float,
                    percentage_conifer=str2float,
                    percentage_dead_balsam_fir=str2float,
                    grass_cure=str2float,
                    crown_base_height=str2float,
                    isi=float,
                    bui=float,
                    ffmc=float,
                    dmc=float,
                    dc=float,
                    fuel_type=str),
    target_fixture='result')
def given_red_app_input(elevation: float,  # pylint: disable=too-many-arguments, invalid-name, too-many-locals
                        latitude: float, longitude: float, time_of_interest: date,
                        wind_speed: float, wind_direction: float,
                        percentage_conifer: float,
                        percentage_dead_balsam_fir: float,
                        grass_cure: float,
                        crown_base_height: float,
                        isi: float, bui: float, ffmc: float, dmc: float, dc: float, fuel_type: str):
    """ Take input and calculate actual and expected results """
    # get python result:
    python_input = FBACalculatorWeatherStation(elevation=elevation,
                                               fuel_type=FuelTypeEnum[fuel_type],
                                               time_of_interest=time_of_interest,
                                               percentage_conifer=percentage_conifer,
                                               percentage_dead_balsam_fir=percentage_dead_balsam_fir,
                                               grass_cure=grass_cure,
                                               crown_base_height=crown_base_height,
                                               crown_fuel_load=None,
                                               lat=latitude, long=longitude, bui=bui,
                                               ffmc=ffmc, isi=isi, fwi=None, wind_speed=wind_speed,
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
        'cfb': java_fbp.cfb / 100.0,  # CFFDRS gives cfb as a fraction
        'hfi': java_fbp.hfi,
        'area': java_fbp.area
    }

    error_dict = {
        'fuel_type': fuel_type
    }

    return {
        'python': python_fba,
        'expected': expected,
        'fuel_type': fuel_type,
        'error': error_dict
    }


@then(parsers.parse("ROS is within {ros_em} ({note})"), converters={'ros_em': float, 'note': str})
def then_ros(result: dict, ros_em: float, note: str):
    """ check the relative error of the ros """
    error = check_metric('ROS',
                         result['fuel_type'],
                         result['python'].ros,
                         result['expected']['ros'],
                         ros_em,
                         note)
    result['error']['ros_em'] = error


@then(parsers.parse("ROS_t is within range ({note})"), converters={'note': str})
def then_ros_t(result: dict, note: str):
    """ check the relative error of the ros """
    check_metric('ROS_t',
                 result['fuel_type'],
                 result['python'].ros_t,
                 result['expected']['ros_t'],
                 acceptable_margin_of_error,
                 note)


@then(parsers.parse("CFB is within {cfb_em} ({note})"), converters={'cfb_em': float, 'note': str})
def then_cfb(result: dict, cfb_em: float, note: str):
    """ check the relative error of the cfb """
    error = check_metric('CFB',
                         result['fuel_type'],
                         result['python'].cfb,
                         result['expected']['cfb'],
                         cfb_em,
                         note)
    result['error']['cfb_em'] = error


@then(parsers.parse("CFB_t is within range ({note})"), converters={'note': str})
def then_cfb_t(result: dict, note: str):
    """ check the relative error of the ros """
    check_metric('CFB_t',
                 result['fuel_type'],
                 result['python'].cfb_t,
                 result['expected']['cfb'],
                 acceptable_margin_of_error,
                 note)


@then(parsers.parse("HFI is within {hfi_em} ({note})"), converters={'hfi_em': float, 'note': str})
def then_hfi(result: dict, hfi_em: float, note: str):
    """ check the relative error of the hfi """
    error = check_metric('HFI',
                         result['fuel_type'],
                         result['python'].hfi,
                         result['expected']['hfi'],
                         hfi_em,
                         note)
    result['error']['hfi_em'] = error


@then(parsers.parse("HFI_t is within range ({note})"), converters={'note': str})
def then_hfi_t(result: dict, note: str):
    """ check the relative error of the ros """
    check_metric('HFI_t',
                 result['fuel_type'],
                 result['python'].hfi_t,
                 result['expected']['hfi'],
                 acceptable_margin_of_error,
                 note)


@then(parsers.parse("1 HR Size is within {one_hr_em} ({note})"), converters={'one_hr_em': float, 'note': str})
def then_one_hr(result: dict, one_hr_em: float, note: str):
    """ check the relative error of the a hour fire size"""
    error = check_metric('1 HR Size',
                         result['fuel_type'],
                         result['python'].sixty_minute_fire_size,
                         result['expected']['area'],
                         one_hr_em,
                         note)
    result['error']['one_hr_em'] = error


@then(parsers.parse("(1 HR Size)_t is within range ({note})"), converters={'note': str})
def then_one_hr_t(result: dict, note: str):
    """ check the relative error of the a hour fire size"""
    check_metric('1 HR Size t',
                 result['fuel_type'],
                 result['python'].sixty_minute_fire_size_t,
                 result['expected']['area'],
                 fire_size_acceptable_margin_of_error,
                 note)


@then("Log it")
def log_it(result: dict):
    """ Log a string matching the scenario input - useful when improving values.  """
    error_dict = result.get('error')
    header = '| fuel_type | elevation | latitude   | longitude    | time_of_interest | wind_speed | wind_direction | percentage_conifer | percentage_dead_balsam_fir | grass_cure | crown_base_height | isi  | bui   | ffmc | dmc   | dc    | one_hr_em | ros_em | hfi_em | cfb_em | note   |'
    header = header.strip('|')
    header = header.split('|')
    header = [x.strip() for x in header]

    line = '|'
    for key in header:
        value = error_dict.get(key, key)
        if isinstance(value, float):
            line += f'{value:.2f}|'
        else:
            line += f'{value}|'
    logger.debug(line)


@pytest.mark.usefixtures('mock_jwt_decode')
@scenario('test_fba_error.feature', 'Fire Behaviour Calculation - vs. Spreadsheet')
def test_fire_behaviour_calculator_spreadsheet_scenario():
    """ BDD Scenario. """


@given(parsers.parse("""Spreadsheet input {elevation}, {latitude}, {longitude}, {time_of_interest}, {wind_speed}, {wind_direction}, """
       """{percentage_conifer}, {percentage_dead_balsam_fir}, {grass_cure}, {crown_base_height}, {isi}, """
                     """{bui}, {ffmc}, {dmc}, {dc}, {fuel_type}, {ros}, {hfi}, {cfb}"""),
       converters=dict(elevation=float,
                       latitude=float,
                       longitude=float,
                       percentage_conifer=str2float,
                       percentage_dead_balsam_fir=str2float,
                       crown_base_height=str2float,
                       grass_cure=str2float,
                       isi=float,
                       bui=float,
                       ffmc=float,
                       dmc=float,
                       dc=float,
                       fuel_type=str,
                       cfb=str2float,
                       hfi=str2float,
                       ros=str2float,
                       time_of_interest=date.fromisoformat,
                       wind_direction=float,
                       wind_speed=float),
       target_fixture='result')
def given_spreadsheet_input(elevation: float,  # pylint: disable=too-many-arguments, invalid-name, too-many-locals
                            latitude: float, longitude: float, time_of_interest: str,
                            wind_speed: float, wind_direction: float,
                            percentage_conifer: float, percentage_dead_balsam_fir: float, grass_cure: float,
                            crown_base_height: float,
                            isi: float, bui: float, ffmc: float, dmc: float, dc: float, fuel_type: str,
                            ros: float, hfi: float, cfb: float):
    """ Take input and calculate actual and expected results """
    # get python result:
    fwi = None
    python_input = FBACalculatorWeatherStation(elevation=elevation,
                                               fuel_type=FuelTypeEnum[fuel_type],
                                               time_of_interest=time_of_interest,
                                               percentage_conifer=percentage_conifer,
                                               percentage_dead_balsam_fir=percentage_dead_balsam_fir,
                                               grass_cure=grass_cure,
                                               crown_base_height=crown_base_height,
                                               crown_fuel_load=None,
                                               lat=latitude,
                                               long=longitude,
                                               bui=bui,
                                               ffmc=ffmc,
                                               isi=isi,
                                               fwi=fwi,
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

    error_dict = {
        'fuel_type': fuel_type
    }

    return {
        'python': python_fba,
        'expected': expected,
        'fuel_type': fuel_type,
        'error': error_dict
    }
