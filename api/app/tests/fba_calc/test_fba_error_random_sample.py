"""
Unit tests for fire behavour calculator.
"""
from datetime import datetime, timezone as dt_tz
import random
from typing import Final
import logging
from pytest_bdd import scenario, given, then, parsers
from app import configure_logging
from app.schemas.fba_calc import FuelTypeEnum
from app.utils.time import get_hour_20_from_date
from app.fire_behaviour.advisory import calculate_fire_behaviour_advisory, FBACalculatorWeatherStation
from app.fire_behaviour.cffdrs import fire_weather_index, initial_spread_index, bui_calc
from app.utils.redapp import FBPCalculateStatisticsCOM
from app.tests.fba_calc import check_metric, fire_size_acceptable_margin_of_error
from app.tests.common import str2float
import pytest


configure_logging()

logger = logging.getLogger(__name__)


def _random_date():
    start = datetime.fromisoformat('2021-01-01')
    end = datetime.fromisoformat('2021-12-31')
    return datetime.fromtimestamp(random.uniform(start.timestamp(), end.timestamp()), tz=dt_tz.utc)


acceptable_margin_of_error: Final = 0.01


@pytest.mark.usefixtures('mock_jwt_decode')
@scenario('test_fba_error_random_sample.feature', 'Fire Behaviour Calculation')
def test_fire_behaviour_calculator_scenario():
    """ BDD Scenario. """


@given(
    parsers.parse("""{fuel_type}, {percentage_conifer}, {percentage_dead_balsam_fir}, {grass_cure} and """
                  """{crown_base_height} for {num_iterations}"""),
    converters=dict(crown_base_height=str2float,
                    fuel_type=str,
                    percentage_conifer=str2float,
                    percentage_dead_balsam_fir=str2float,
                    grass_cure=str2float,
                    num_iterations=int),
    target_fixture='results'
)
def given_input(fuel_type: str, percentage_conifer: float, percentage_dead_balsam_fir: float,
                grass_cure: float, crown_base_height: float, num_iterations: int):
    """ Take input and calculate actual and expected results """

    # get python result:
    # seed = time()
    seed = 43
    logger.info('using random seed: %s', seed)
    random.seed(seed)
    results = []
    for index in range(num_iterations):
        # pylint: disable=invalid-name
        elevation = random.randint(0, 4019)
        latitude = random.uniform(45, 60)
        longitude = random.uniform(-118, -136)
        time_of_interest = _random_date()
        # NOTE: For high wind speeds, the difference between REDapp and FireBAT starts exceeding
        # tolerances. REDapp calculates it's own ISI (doesn't take the one provided by the system),
        # but uses a different formula from CFFDRS, so the results start getting more pronounced
        # with higher wind speeds. For that reason we limit our wind speeds to 40 km/h, since anything
        # above that starts failing the unit tests.
        wind_speed = random.uniform(0, 40)
        wind_direction = random.uniform(0, 360)
        temperature = random.uniform(0, 49.6)  # Lytton, B.C., 2021
        relative_humidity = random.uniform(0, 100)
        precipitation = random.uniform(0, 50)
        dc = random.uniform(0, 600)
        dmc = random.uniform(11, 205)
        bui = bui_calc(dmc, dc)
        ffmc = random.uniform(11, 100)
        isi = initial_spread_index(ffmc, wind_speed)
        fwi = fire_weather_index(isi, bui)

        message = (f"""({index}) elevation:{elevation} ; lat: {latitude} ; lon: {longitude}; """
                   f"""toi: {time_of_interest}; ws: {wind_speed}; wd: {wind_direction}; """
                   f"""temperature: {temperature}; relative_humidity: {relative_humidity}; """
                   f"""precipitation: {precipitation}; dc: {dc}; dmc: {dmc}; bui: {bui}; """
                   f"""ffmc: {ffmc}; isi: {isi}""")
        logger.debug(message)

        test_entry = (f"""({index}) | {fuel_type} | {elevation} | {latitude} | {longitude} | """
                      f"""{time_of_interest} | {wind_speed} | {wind_direction} | {percentage_conifer} | """
                      f"""{percentage_dead_balsam_fir} | {grass_cure} | {crown_base_height} | {isi}  | """
                      f"""{bui} | {ffmc} | {dmc} | {dc} | 0.01 | 0.01 | 0.01 | 0.01 | None | 0.01 | """
                      f"""None | 0.01 | None | 0.01 | |""")
        logger.debug(test_entry)
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
                                                   temperature=temperature,
                                                   relative_humidity=relative_humidity,
                                                   precipitation=precipitation,
                                                   status='Forecasted',
                                                   prev_day_daily_ffmc=None,
                                                   last_observed_morning_rh_values=None)
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

        error_dict = {
            'fuel_type': fuel_type
        }
        results.append(
            {
                'input': {'isi': isi, 'bui': bui, 'wind_speed': wind_speed, 'ffmc': ffmc},
                'python': python_fba,
                'java': java_fbp,
                'fuel_type': fuel_type,
                'error': error_dict
            }
        )

    return results


@then(parsers.parse("ROS is within {ros_margin_of_error} compared to REDapp"),
      converters={'ros_margin_of_error': float})
def then_ros_good(results: list, ros_margin_of_error: float):
    """ check the relative error of ROS """
    for index, result in enumerate(results):
        wind_speed = result['input']['wind_speed']
        ffmc = result['input']['ffmc']
        isi = result['input']['isi']
        bui = result['input']['bui']
        java_isi = result['java'].isi
        # assumptions:
        # ros_eq == ROScalc
        # ros_t  == ROStcalc
        error = check_metric('ROS',
                             result['fuel_type'],
                             result['python'].ros,
                             result['java'].ros_eq,
                             ros_margin_of_error,
                             f"""({index}) input- isi:{isi}; bui:{bui}; wind_speed:{wind_speed}; ffmc:{ffmc}; """
                             f"""java - isi:{java_isi}""")
        result['error']['ros_margin_of_error'] = error


@then("ROS_t is within range")
def then_ros_t(results: list):
    """ check the relative error of the ros """
    for result in results:
        check_metric('ROS_t',
                     result['fuel_type'],
                     result['python'].ros_t,
                     result['java'].ros_t,
                     acceptable_margin_of_error)


@then(parsers.parse("HFI is within {hfi_margin_of_error} compared to REDapp"),
      converters={'hfi_margin_of_error': float})
def then_hfi_good(results: list, hfi_margin_of_error: float):
    """ check the relative error of HFI """
    for index, result in enumerate(results):
        error = check_metric('HFI',
                             result['fuel_type'],
                             result['python'].hfi,
                             result['java'].hfi,
                             hfi_margin_of_error,
                             f'({index})')
        result['error']['hfi_margin_of_error'] = error


@then("HFI_t is within range")
def then_hfi_t(results: list):
    """ check the relative error of the ros """
    for result in results:
        check_metric('HFI_t',
                     result['fuel_type'],
                     result['python'].hfi_t,
                     result['java'].hfi,
                     acceptable_margin_of_error)


@then(parsers.parse("CFB is within {cfb_margin_of_error} compared to REDapp"),
      converters={'cfb_margin_of_error': float})
def then_cfb_good(results: list, cfb_margin_of_error: float):
    """ check the relative error of HFI """
    for index, result in enumerate(results):
        error = check_metric('CFB',
                             result['fuel_type'],
                             result['python'].cfb * 100.0,
                             result['java'].cfb, cfb_margin_of_error,
                             f'({index})')
        result['error']['cfb_margin_of_error'] = error


@then(parsers.parse("CFB_t is within range of {cfb_t_margin_of_error} compared to REDapp"),
      converters={'cfb_t_margin_of_error': float})
def then_cfb_t(results: list, cfb_t_margin_of_error: float):
    """ check the relative error of the ros """
    for result in results:
        check_metric('CFB_t',
                     result['fuel_type'],
                     result['python'].cfb_t * 100.0,
                     result['java'].cfb,
                     cfb_t_margin_of_error)


@then(parsers.parse("1 Hour Spread is within {one_hour_spread_margin_of_error} compared to REDapp"),
      converters={'one_hour_spread_margin_of_error': float})
def then_1_hour_spread_good(results: list, one_hour_spread_margin_of_error: float):
    """ check the relative error of HFI """
    for index, result in enumerate(results):
        error = check_metric('one_hour_size',
                             result['fuel_type'],
                             result['python'].sixty_minute_fire_size,
                             result['java'].area, one_hour_spread_margin_of_error,
                             f'({index})')
        result['error']['one_hour_spread_margin_of_error'] = error


@then("(1 HR Size)_t is within range")
def then_one_hour_size_t(results: list):
    """ check the relative error of the ros """
    for result in results:
        check_metric('1 HR Size t',
                     result['fuel_type'],
                     result['python'].sixty_minute_fire_size_t,
                     result['java'].area,
                     fire_size_acceptable_margin_of_error)


@then("Log it")
def log_it(results: list):
    """ Log a string matching the scenario input - useful when improving values.  """
    keys = ('one_hour_spread_margin_of_error', 'cfb_margin_of_error',
            'hfi_margin_of_error', 'ros_margin_of_error')
    values = {}
    for key in keys:
        values[key] = 0.01
    for result in results:
        error_dict = result.get('error')
        for key in keys:
            old_value = values.get(key)
            if error_dict[key] > old_value:
                values[key] = error_dict[key]
        values['fuel_type'] = error_dict['fuel_type']

    header = ("""| fuel_type | percentage_conifer | percentage_dead_balsam_fir | grass_cure | """
              """crown_base_height | ros_margin_of_error | hfi_margin_of_error | cfb_margin_of_error | """
              """one_hour_spread_margin_of_error | num_iterations |""")
    header = header.strip('|')
    header = header.split('|')
    header = [x.strip() for x in header]

    line = '|'
    for key in header:
        value = values.get(key, key)
        if isinstance(value, float):
            line += f'{value:.2f}|'
        else:
            line += f'{value}|'
    logger.debug(line)
