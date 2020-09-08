""" Functional testing for /models/{model}/predictions/ endpoint.
"""
import logging
from datetime import datetime
import os
import json
from pytest_bdd import scenario, given, then, when
from fastapi.testclient import TestClient
import pytest
from alchemy_mock.mocking import UnifiedAlchemyMagicMock
import app.main
from app.db.models import (PredictionModel, WeatherStationModelPrediction)
from app.schemas import (WeatherStation, WeatherModelRun,
                         WeatherModelPrediction, WeatherModelPredictionValues)

LOGGER = logging.getLogger(__name__)


@pytest.fixture()
def mock_session(monkeypatch, data):
    """ Mocked out sqlalchemy session """
    if data:
        dirname = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(dirname, data)
        with open(filename) as data_file:
            json_data = json.load(data_file)

        def mock_get_session(*args):
            mock_session = UnifiedAlchemyMagicMock()
            return mock_session

        def mock_get_weather_station_model_predictions(*args):
            station_data = {
                "code": 322,
                "name": "AFTON",
                "lat": 50.6733333,
                "long": -120.4816667,
                "ecodivision_name": "SEMI-ARID STEPPE HIGHLANDS",
                "core_season": {
                    "start_month": 5,
                    "start_day": 1,
                    "end_month": 9,
                    "end_day": 15
                }
            }
            model_run_data = {
                "datetime": "2020-08-31T00:00:00+00:00",
                "name": "Global Deterministic Prediction System",
                "abbreviation": "GDPS",
                "projection": "latlon.15x.15"
            }
            station = WeatherStation(code=station_data['code'], name=station_data['name'], lat=station_data['lat'],
                                     long=station_data['long'], ecodivision_name=station_data['ecodivision_name'], core_season=station_data['core_season'])
            model_run = WeatherModelRun(datetime=model_run_data['datetime'], name=model_run_data['name'],
                                        abbreviation=model_run_data['abbreviation'], projection=model_run_data['projection'])
            result = []
            for prediction in json_data['predictions']:
                prediction = WeatherModelPredictionValues(
                    temperature=prediction['tmp_tgl_2'], relative_humidity=prediction['rh_tgl_2'], datetime=prediction['prediction_timestamp'])
                result.append(WeatherModelPrediction(station=station,
                                                     model_run=model_run, values=[prediction]))
            return result

        monkeypatch.setattr(app.db.database, 'get_session', mock_get_session)
        monkeypatch.setattr(app.db.crud, 'get_most_recent_historic_station_model_predictions',
                            mock_get_weather_station_model_predictions)


@scenario("test_most_recent_historic_predictions.feature", "Get most recent historic model predictions from database for selected stations")
def test_db_predictions_scenario():
    """ BDD Scenario for predictions """


@given("A database with <data>")
def given_a_database(mock_session, data):
    """ Bind the data variable """
    return {}


@given("station <codes>")
def given_stations(codes):
    return eval(codes)


@given("starting date range of <start_date>")
def given_starting_date_range(start_date):
    return eval(start_date)


@given("ending date range of <end_date>")
def given_ending_date_range(end_date):
    return eval(end_date)


@when("I call <endpoint>")
def when_predictions(mock_jwt_decode, given_a_database, given_stations, given_starting_date_range, given_ending_date_range, endpoint: str):
    client = TestClient(app.main.app)
    response = client.post(
        endpoint, headers={'Authorization': 'Bearer token'}, json={'stations': given_stations, 'start_date': given_starting_date_range, 'end_date': given_ending_date_range})
    given_a_database['response_json'] = response.json()


@then('There are <num_prediction_values>')
def assert_num_predictions(given_a_database, num_prediction_values):
    """ There are 4 predictions in the database, but only 3 should be returned, since once prediction is an update over a previously issued model run. """
    num_prediction_values = eval(num_prediction_values)
    assert len(given_a_database['response_json']['predictions']) == num_prediction_values['len']


@then('The <expected_response> is matched')
def assert_response(given_a_database, expected_response):
    """ "Catch all" test that blindly checks the actual json response against an expected response. """
    dirname = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(dirname, expected_response)
    with open(filename) as data_file:
        expected_json = json.load(data_file)
        assert given_a_database['response_json'] == expected_json
