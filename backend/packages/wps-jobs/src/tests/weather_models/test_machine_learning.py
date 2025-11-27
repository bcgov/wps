from datetime import datetime
import pytest
from wps_shared.db.models.observations import HourlyActual
from weather_model_jobs import machine_learning
from tests.weather_models.crud import (
    get_actuals_left_outer_join_with_predictions,
    get_accumulated_precip_by_24h_interval,
    get_predicted_daily_precip,
)
from wps_shared.db.models.weather_models import ModelRunPrediction, PredictionModel
from weather_model_jobs.machine_learning import StationMachineLearning
import math


@pytest.fixture()
def mock_get_actuals_left_outer_join_with_predictions(monkeypatch):
    """Mock out call to DB returning actuals macthed with predictions"""
    monkeypatch.setattr(
        machine_learning,
        "get_actuals_left_outer_join_with_predictions",
        get_actuals_left_outer_join_with_predictions,
    )


@pytest.fixture()
def mock_get_accumulated_precip_by_24h_interval(monkeypatch):
    """Mock out call to DB returning actual 24 hour precipitation data"""
    monkeypatch.setattr(
        machine_learning,
        "get_accumulated_precip_by_24h_interval",
        get_accumulated_precip_by_24h_interval,
    )


@pytest.fixture()
def mock_get_predicted_daily_precip(monkeypatch):
    """Mock out call to DB returning modelled/predicted 24 hour precipitation data"""
    monkeypatch.setattr(machine_learning, "get_predicted_daily_precip", get_predicted_daily_precip)


def test_bias_adjustment_with_samples(
    mock_get_actuals_left_outer_join_with_predictions,
    mock_get_accumulated_precip_by_24h_interval,
    mock_get_predicted_daily_precip,
):
    predict_date_with_samples = datetime.fromisoformat("2020-09-03T21:14:51.939836+00:00")

    machine_learner = StationMachineLearning(
        session=None,
        model=PredictionModel(id=1),
        target_coordinate=[-120.4816667, 50.6733333],
        station_code=None,
        max_learn_date=datetime.now(),
    )
    machine_learner.learn()

    temp_result = machine_learner.predict_temperature(20, predict_date_with_samples)
    rh_result = machine_learner.predict_rh(50, predict_date_with_samples)
    wdir_result = machine_learner.predict_wind_direction(10, 120, predict_date_with_samples)
    precip_result = machine_learner.predict_precipitation(3, datetime(2023, 10, 26, 20, 0, 0))
    assert temp_result == 30
    assert rh_result == 100
    assert math.isclose(wdir_result, 115.51556685719027)
    assert precip_result == 3


def test_bias_adjustment_of_rh_above_100(
    monkeypatch, mock_get_accumulated_precip_by_24h_interval, mock_get_predicted_daily_precip
):
    def get_actuals_and_predictions_with_high_rh(*args):
        """Two actual/prediction pairs to force a prediction of rh above 100."""
        return [
            [
                HourlyActual(
                    weather_date=datetime(2020, 10, 10, 18),
                    temperature=20,
                    temp_valid=True,
                    wind_speed=10,
                    wind_direction=90,
                    relative_humidity=105,
                    rh_valid=True,
                ),
                ModelRunPrediction(
                    tmp_tgl_2=2,
                    rh_tgl_2=105,
                    apcp_sfc_0=2,
                    wind_tgl_10=11,
                    wdir_tgl_10=97,
                    prediction_timestamp=datetime(2020, 10, 10, 18),
                ),
            ],
            [
                HourlyActual(
                    weather_date=datetime(2020, 10, 10, 21),
                    temperature=30,
                    temp_valid=True,
                    wind_speed=12,
                    wind_direction=120,
                    relative_humidity=105,
                    rh_valid=True,
                ),
                ModelRunPrediction(
                    tmp_tgl_2=1,
                    rh_tgl_2=105,
                    apcp_sfc_0=3,
                    wind_tgl_10=11,
                    wdir_tgl_10=101,
                    prediction_timestamp=datetime(2020, 10, 10, 21),
                ),
            ],
        ]

    monkeypatch.setattr(
        machine_learning,
        "get_actuals_left_outer_join_with_predictions",
        get_actuals_and_predictions_with_high_rh,
    )

    predict_date_with_samples = datetime.fromisoformat("2020-09-03T21:14:51.939836+00:00")

    machine_learner = StationMachineLearning(
        session=None,
        model=PredictionModel(id=1),
        target_coordinate=[-120.4816667, 50.6733333],
        station_code=None,
        max_learn_date=datetime.now(),
    )
    machine_learner.learn()

    rh_result = machine_learner.predict_rh(105, predict_date_with_samples)
    assert rh_result == 100


def test_bias_adjustment_without_samples(
    mock_get_actuals_left_outer_join_with_predictions,
    mock_get_accumulated_precip_by_24h_interval,
    mock_get_predicted_daily_precip,
):
    predict_date_without_samples = datetime.fromisoformat("2020-09-03T01:14:51.939836+00:00")

    machine_learner = StationMachineLearning(
        session=None,
        model=PredictionModel(id=1),
        target_coordinate=[-120.4816667, 50.6733333],
        station_code=None,
        max_learn_date=datetime.now(),
    )
    machine_learner.learn()

    temp_result = machine_learner.predict_temperature(20, predict_date_without_samples)
    rh_result = machine_learner.predict_rh(50, predict_date_without_samples)
    wdir_result = machine_learner.predict_wind_direction(10, 290, predict_date_without_samples)
    precip_result = machine_learner.predict_precipitation(3, predict_date_without_samples)
    assert temp_result is None
    assert rh_result is None
    assert wdir_result is None
    assert precip_result is None
