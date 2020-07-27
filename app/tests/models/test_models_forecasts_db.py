""" Functional testing for /models/{model}/forecasts/ endpoint.
"""
import logging
from datetime import datetime
import os
import json
from pytest_bdd import scenario, given, then, when
from fastapi.testclient import TestClient
import pytest
import shapely.wkt
from geoalchemy2.shape import from_shape
from alchemy_mock.mocking import UnifiedAlchemyMagicMock
import app.main
from app.db.models import (PredictionModelRun, PredictionModel, ModelRunGridSubsetPrediction,
                           PredictionModelGridSubset)

LOGGER = logging.getLogger(__name__)

# pylint: disable=unused-argument, redefined-outer-name, eval-used


@pytest.fixture()
def mock_session(monkeypatch, data):
    """ Mocked out sqlalchemy session """
    if data:
        dirname = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(dirname, data)
        with open(filename) as data_file:
            json_data = json.load(data_file)

        predictions = json_data['predictions']
        geometry = json_data['geometry']

        prediction_model = PredictionModel(
            id=1, name='name', abbreviation='abbrev', projection='projection')

        def mock_get_session(*args):
            mock_session = UnifiedAlchemyMagicMock()
            return mock_session

        def mock_get_most_recent_model_run(*args) -> PredictionModelRun:
            return PredictionModelRun(id=1,
                                      prediction_model=prediction_model,
                                      prediction_run_timestamp=datetime.fromisoformat('2020-01-22T18:00:00+00:00'))

        def mock_get_model_run_predictions(*args):
            shape = shapely.wkt.loads(geometry)
            grid = PredictionModelGridSubset(
                id=1,
                prediction_model_id=prediction_model.id,
                prediction_model=prediction_model,
                geom=from_shape(shape)
            )
            result = []
            for prediction in predictions:
                prediction['prediction_timestamp'] = datetime.fromisoformat(
                    prediction['prediction_timestamp'])
                result.append(
                    (grid, ModelRunGridSubsetPrediction(**prediction)))
            return result
        monkeypatch.setattr(app.db.database, 'get_session', mock_get_session)
        monkeypatch.setattr(app.db.crud, 'get_most_recent_model_run',
                            mock_get_most_recent_model_run)
        monkeypatch.setattr(app.db.crud, 'get_model_run_predictions',
                            mock_get_model_run_predictions)


@ scenario("test_models_forecasts_db.feature", "Get model forecasts from database",
           example_converters=dict(codes=str, data=str, num_forecast_values=str))
def test_db_forecasts_scenario():
    """ BDD Scenario. """


@given("A database with <data>")
def given_a_database(mock_session, data):
    """ Bind the data variable """
    return {}


@given("station <codes>")
def given_stations(codes):
    return eval(codes)


@when("I call /models/{model}/forecasts/")
def when_forecasts(mock_jwt_decode, given_a_database, given_stations):
    client = TestClient(app.main.app)
    response = client.post(
        '/models/GDPS/forecasts/', headers={'Authorization': 'Bearer token'}, json={'stations': given_stations})
    given_a_database['response_json'] = response.json()


@ then('There are <num_forecast_values>')
def assert_num_forecasts(given_a_database, num_forecast_values):
    """ Even though there are only two predictions in the database, we expect an interpolated noon value. """
    num_forecast_values = eval(num_forecast_values)
    assert len(given_a_database['response_json']['forecasts']
               [num_forecast_values['index']]['values']) == num_forecast_values['len']


@then('The <expected_response> is matched')
def assert_response(given_a_database, expected_response):
    """ "Catch all" test that blindly checks the actual json response against an expected response. """
    dirname = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(dirname, expected_response)
    with open(filename) as data_file:
        expected_json = json.load(data_file)
        assert given_a_database['response_json'] == expected_json
