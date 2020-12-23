""" BDD tests for processing file from env. Canada. """
import logging
import datetime
import json
from typing import List
from pytest_bdd import scenario, given, then, when
from app.weather_models.fetch.predictions import NoonInterpolator


logger = logging.getLogger(__name__)


@scenario('test_noon_calculator.feature', 'Calculate noon data',
          example_converters=dict(data=json.loads, timestamp=str, temperature=float, relative_humidity=float,
                                  delta_precipitation=float))
def test_noon_calculator():
    """ BDD Scenario. """


@given('<data>', target_fixture='result')
def given_data(data: List):
    """ Prepare fixture with data """
    return {'data': data}


@when('processed')
def processed(result: dict):
    """ Process data """
    interpolator = NoonInterpolator()
    for item in result['data']:
        timestamp = datetime.datetime.fromisoformat(item['datetime'])
        for key, value in item['values'].items():
            interpolator.update(key, value, timestamp)
    result['noon_value'] = interpolator.calculate_noon_value()


@then('assert <timestamp> <temperature> <relative_humidity> <delta_precipitation>')
def then_assert(result: dict, timestamp: str, temperature: float,
                relative_humidity: float, delta_precipitation: float):
    """ Assert values are as expected """
    assert result['noon_value'].datetime == datetime.datetime.fromisoformat(timestamp)
    assert result['noon_value'].temperature == temperature
    assert result['noon_value'].relative_humidity == relative_humidity
    assert result['noon_value'].delta_precipitation == delta_precipitation
