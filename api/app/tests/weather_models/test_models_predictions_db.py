""" Functional testing for /models/{model}/predictions/ endpoint.
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
from app.db.models import (PredictionModelRunTimestamp, PredictionModel, ModelRunGridSubsetPrediction,
                           PredictionModelGridSubset)

LOGGER = logging.getLogger(__name__)


@pytest.fixture(name='mock_session')
def mock_session_fixture(monkeypatch, data):
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

        # pylint: disable=unused-argument
        def mock_get_session(*args):
            return UnifiedAlchemyMagicMock()

        def mock_get_most_recent_model_run(*args) -> PredictionModelRunTimestamp:
            timestamp = '2020-01-22T18:00:00+00:00'
            return PredictionModelRunTimestamp(id=1,
                                               prediction_model=prediction_model,
                                               prediction_run_timestamp=datetime.fromisoformat(timestamp))

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
        monkeypatch.setattr(
            app.db.database, 'get_read_session', mock_get_session)
        monkeypatch.setattr(app.db.crud.weather_models, 'get_most_recent_model_run',
                            mock_get_most_recent_model_run)
        monkeypatch.setattr(app.db.crud.weather_models, 'get_model_run_predictions',
                            mock_get_model_run_predictions)


@pytest.mark.usefixtures("mock_jwt_decode")
@scenario("test_models_predictions_db.feature", "Get model predictions from database")
def test_db_predictions_scenario():
    """ BDD Scenario for predictions """


@given("A database with <data>", target_fixture='context')
def given_a_database(data):
    """ Bind the data variable """
    assert data
    return {}


@given("station <codes>", target_fixture='stations')
def given_stations(codes):
    """ Turn provided string into array of codes. """
    return eval(codes)  # pylint: disable=eval-used


@when("I call <endpoint>")
def when_predictions(context, stations, endpoint: str):
    """ post to endpoint """
    client = TestClient(app.main.app)
    response = client.post(
        endpoint, headers={'Authorization': 'Bearer token'}, json={'stations': stations})
    context['response_json'] = response.json()


@then('There are <num_prediction_values>')
def assert_num_predictions(context, num_prediction_values):
    """ Even though there are only two predictions in the database, we expect an interpolated noon value. """
    num_prediction_values = eval(num_prediction_values)  # pylint: disable=eval-used
    assert len(context['response_json']['predictions']
               [num_prediction_values['index']]['values']) == num_prediction_values['len']


@then('The <expected_response> is matched')
def assert_response(context, expected_response):
    """ "Catch all" test that blindly checks the actual json response against an expected response. """
    dirname = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(dirname, expected_response)
    with open(filename) as data_file:
        expected_json = json.load(data_file)
        assert context['response_json'] == expected_json
