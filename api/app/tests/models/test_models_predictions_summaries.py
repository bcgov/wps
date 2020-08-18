""" Functional testing for /models/{model}/predictions/ endpoint.
"""
from datetime import datetime
import os
import json
from pytest_bdd import scenario, given, then, when
from fastapi.testclient import TestClient
import pytest
import shapely.wkt
from geoalchemy2.shape import from_shape
from alchemy_mock.mocking import UnifiedAlchemyMagicMock
from alchemy_mock.compat import mock
import app.main
from app.db.models import (PredictionModelRunTimestamp, PredictionModel, ModelRunGridSubsetPrediction,
                           PredictionModelGridSubset)


@pytest.fixture()
def mock_session(monkeypatch):
    """ Mocked out sqlalchemy session """
    def mock_get_session(*args):

        prediction_model = PredictionModel(id=1,
                                           abbreviation='GDPS',
                                           projection='latlon.15x.15',
                                           name='Global Deterministic Prediction System')

        geometry = ("POLYGON ((-120.525 50.77500000000001, -120.375 50.77500000000001,"
                    "-120.375 50.62500000000001, -120.525 50.62500000000001, -120.525 50.77500000000001))")
        shape = shapely.wkt.loads(geometry)

        grid = PredictionModelGridSubset(
            id=1,
            prediction_model_id=prediction_model.id,
            prediction_model=prediction_model,
            geom=from_shape(shape)
        )

        date_1 = "2020-07-22T18:00:00+00:00"
        date_2 = "2020-07-22T20:00:00+00:00"
        data = [
            (
                [mock.call.query(PredictionModelGridSubset,
                                 ModelRunGridSubsetPrediction, PredictionModel)],
                [
                    # 3 on the same hour, testing interpolation and percentiles.
                    [grid, ModelRunGridSubsetPrediction(
                        prediction_model_grid_subset_id=grid.id,
                        prediction_timestamp=datetime.fromisoformat(date_1),
                        tmp_tgl_2=[10, 11, 12, 13],
                        rh_tgl_2=[20, 30, 40, 50]), prediction_model],
                    [grid, ModelRunGridSubsetPrediction(
                        prediction_model_grid_subset_id=grid.id,
                        prediction_timestamp=datetime.fromisoformat(date_1),
                        tmp_tgl_2=[11, 12, 13, 14],
                        rh_tgl_2=[30, 40, 50, 60]), prediction_model],
                    [grid, ModelRunGridSubsetPrediction(
                        prediction_model_grid_subset_id=grid.id,
                        prediction_timestamp=datetime.fromisoformat(date_1),
                        tmp_tgl_2=[9, 10, 11, 12],
                        rh_tgl_2=[20, 30, 40, 50]), prediction_model],
                    # 1 on the hour, testing it remains unchanged.
                    [grid, ModelRunGridSubsetPrediction(
                        prediction_model_grid_subset_id=grid.id,
                        prediction_timestamp=datetime.fromisoformat(
                            "2020-07-22T19:00:00+00:00"),
                        tmp_tgl_2=[9, 9, 9, 9],
                        rh_tgl_2=[20, 20, 20, 20]), prediction_model],
                    # 3 on same hour, same values at each grid point for easy percentile testing.
                    [grid, ModelRunGridSubsetPrediction(
                        prediction_model_grid_subset_id=grid.id,
                        prediction_timestamp=datetime.fromisoformat(date_2),
                        tmp_tgl_2=[9, 9, 9, 9],
                        rh_tgl_2=[20, 20, 20, 20]), prediction_model],
                    [grid, ModelRunGridSubsetPrediction(
                        prediction_model_grid_subset_id=grid.id,
                        prediction_timestamp=datetime.fromisoformat(date_2),
                        tmp_tgl_2=[10, 10, 10, 10],
                        rh_tgl_2=[21, 21, 21, 21]), prediction_model],
                    [grid, ModelRunGridSubsetPrediction(
                        prediction_model_grid_subset_id=grid.id,
                        prediction_timestamp=datetime.fromisoformat(date_2),
                        tmp_tgl_2=[11, 11, 11, 11],
                        rh_tgl_2=[22, 22, 22, 22]), prediction_model]
                ]
            )
        ]
        mock_session = UnifiedAlchemyMagicMock(data=data)
        return mock_session

    monkeypatch.setattr(app.db.database, 'get_session', mock_get_session)


@ scenario("test_models_predictions_summaries.feature", "Get model prediction summaries from database")
def test_model_predictions_summaries_scenario():
    """ BDD Scenario for prediction summaries """


@ given("A database")
def given_a_database(mock_session):
    """ Bind the data variable """
    return {}


@ given("station <codes>")
def given_stations(codes):
    return eval(codes)


@ when("I call <endpoint>")
def when_prediction(mock_jwt_decode, given_a_database, given_stations, endpoint: str):
    client = TestClient(app.main.app)
    response = client.post(
        endpoint, headers={'Authorization': 'Bearer token'}, json={'stations': given_stations})
    given_a_database['response_json'] = response.json()


@ then('The <expected_response> is matched')
def assert_response(given_a_database, expected_response):
    """ "Catch all" test that blindly checks the actual json response against an expected response. """
    dirname = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(dirname, expected_response)
    with open(filename) as data_file:
        expected_json = json.load(data_file)
        assert given_a_database['response_json'] == expected_json
