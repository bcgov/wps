""" Functional testing for /models/{model}/predictions/ endpoint.
"""
import logging
import os
import json
import datetime
from pytest_bdd import scenario, given, then, when
from fastapi.testclient import TestClient
import pytest
from alchemy_mock.mocking import UnifiedAlchemyMagicMock
import app.main
from app.db.models import (
    PredictionModel, WeatherStationModelPrediction, PredictionModelRunTimestamp)

LOGGER = logging.getLogger(__name__)

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f%z'


@pytest.fixture()
def mock_session(monkeypatch, data):
    """ Mocked out sqlalchemy session """
    if data:
        dirname = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(dirname, data)
        with open(filename) as data_file:
            json_data = json.load(data_file)
            # convert strings to datetime
            for item in json_data['predictions']:
                item['prediction_timestamp'] = datetime.datetime.strptime(
                    item['prediction_timestamp'], DATETIME_FORMAT)
                item['create_date'] = datetime.datetime.strptime(
                    item['create_date'], DATETIME_FORMAT)
                item['update_date'] = datetime.datetime.strptime(
                    item['update_date'], DATETIME_FORMAT)
                item['prediction_model_run_timestamp'] = datetime.datetime.strptime(
                    item['prediction_model_run_timestamp'], DATETIME_FORMAT)

        def mock_get_session(*args):  # pylint: disable=unused-argument
            return UnifiedAlchemyMagicMock()

        def mock_get_weather_station_model_predictions(*args):  # pylint: disable=unused-argument
            prediction_model = PredictionModel(
                name='Global Deterministic Prediction System',
                abbreviation='GDPS',
                projection='latlon.15x.15'
            )

            result = []
            for prediction in json_data['predictions']:
                prediction_model_run_timestamp = PredictionModelRunTimestamp(
                    prediction_model_id=1,
                    prediction_run_timestamp=prediction['prediction_model_run_timestamp'],
                    complete=True,
                    interpolated=True
                )
                result.append((WeatherStationModelPrediction(**prediction),
                               prediction_model_run_timestamp, prediction_model))
            return result

        monkeypatch.setattr(
            app.db.database, 'get_read_session', mock_get_session)
        monkeypatch.setattr(app.db.crud.weather_models, 'get_station_model_predictions',
                            mock_get_weather_station_model_predictions)


@scenario("test_most_recent_historic_predictions.feature",
          "Get most recent historic model predictions from database for selected stations")
def test_db_predictions_scenario():
    """ BDD Scenario for predictions """


@given("A database with <data>")
def given_a_database(mock_session, data):  # pylint: disable=redefined-outer-name, unused-argument
    """ Bind the data variable """
    return {}


@given("station <codes>")
def given_stations(codes):
    """ Evaluate string and return array of station codes. """
    return eval(codes)  # pylint: disable=eval-used


@given("starting date range of <start_date>")
def given_starting_date_range(start_date):
    """ Evaluate string and return date """
    return eval(start_date)  # pylint: disable=eval-used


@given("ending date range of <end_date>")
def given_ending_date_range(end_date):
    """ Evaluate string and return date """
    return eval(end_date)  # pylint: disable=eval-used


# pylint: disable=redefined-outer-name, unused-argument
@when("I call <endpoint>")
def when_predictions(mock_jwt_decode,  # pylint: disable=too-many-arguments
                     given_a_database,
                     given_stations,
                     given_starting_date_range,
                     given_ending_date_range,
                     endpoint: str):
    """ post request to endpoint """
    client = TestClient(app.main.api)
    response = client.post(
        endpoint, headers={'Authorization': 'Bearer token'},
        json={
            'stations': given_stations,
            'start_date': given_starting_date_range,
            'end_date': given_ending_date_range})
    given_a_database['response_json'] = response.json()
# pylint: enable=redefined-outer-name, unused-argument


@then('There are <num_prediction_values>')
def assert_num_predictions(given_a_database, num_prediction_values):  # pylint: disable=redefined-outer-name
    """ There are 4 predictions in the database, but only 3 should be returned, since once prediction is an
    update over a previously issued model run. """
    num_prediction_values = eval(num_prediction_values)  # pylint: disable=eval-used
    assert len(given_a_database['response_json']
               ['predictions']) == num_prediction_values['len']


@then('The <expected_response> is matched')
def assert_response(given_a_database, expected_response):  # pylint: disable=redefined-outer-name
    """ "Catch all" test that blindly checks the actual json response against an expected response. """
    dirname = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(dirname, expected_response)
    with open(filename) as data_file:
        expected_json = json.load(data_file)
        assert given_a_database['response_json'] == expected_json
