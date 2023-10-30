from datetime import datetime
import pytest
from app.weather_models import machine_learning
from app.tests.weather_models.crud import (get_actuals_left_outer_join_with_predictions,
                                           get_accumulated_precip_by_24h_interval,
                                           get_predicted_daily_precip)
from app.db.models.weather_models import PredictionModel
from app.weather_models.machine_learning import StationMachineLearning


@pytest.fixture()
def mock_get_actuals_left_outer_join_with_predictions(monkeypatch):
    """ Mock out call to DB returning actuals macthed with predictions """
    monkeypatch.setattr(machine_learning, 'get_actuals_left_outer_join_with_predictions',
                        get_actuals_left_outer_join_with_predictions)
    
@pytest.fixture()
def mock_get_accumulated_precip_by_24h_interval(monkeypatch):
    """ Mock out call to DB returning actual 24 hour precipitation data """
    monkeypatch.setattr(machine_learning, 'get_accumulated_precip_by_24h_interval',
                        get_accumulated_precip_by_24h_interval)
    

@pytest.fixture()
def mock_get_predicted_daily_precip(monkeypatch):
    """ Mock out call to DB returning modelled/predicted 24 hour precipitation data """
    monkeypatch.setattr(machine_learning, 'get_predicted_daily_precip',
                        get_predicted_daily_precip)

def test_bias_adjustment_with_samples(mock_get_actuals_left_outer_join_with_predictions,
                                      mock_get_accumulated_precip_by_24h_interval,
                                      mock_get_predicted_daily_precip):
    predict_date_with_samples = datetime.fromisoformat("2020-09-03T21:14:51.939836+00:00")

    machine_learner = StationMachineLearning(
        session=None,
        model=PredictionModel(id=1),
        target_coordinate=[
            -120.4816667,
            50.6733333
        ],
        station_code=None,
        max_learn_date=datetime.now())
    machine_learner.learn()

    temp_result = machine_learner.predict_temperature(20, predict_date_with_samples)
    rh_result = machine_learner.predict_rh(50, predict_date_with_samples)
    wdir_result = machine_learner.predict_wind_direction(10, 120, predict_date_with_samples)
    precip_result = machine_learner.predict_precipitation(3, datetime(2023,10,26,20,0,0))
    assert temp_result == 30
    assert rh_result == 100
    assert wdir_result == 120
    assert precip_result == 3


def test_bias_adjustment_without_samples(mock_get_actuals_left_outer_join_with_predictions,
                                         mock_get_accumulated_precip_by_24h_interval,
                                         mock_get_predicted_daily_precip):
    predict_date_without_samples = datetime.fromisoformat("2020-09-03T01:14:51.939836+00:00")

    machine_learner = StationMachineLearning(
        session=None,
        model=PredictionModel(id=1),
        target_coordinate=[
            -120.4816667,
            50.6733333
        ],
        station_code=None,
        max_learn_date=datetime.now())
    machine_learner.learn()

    temp_result = machine_learner.predict_temperature(20, predict_date_without_samples)
    rh_result = machine_learner.predict_rh(50, predict_date_without_samples)
    wdir_result = machine_learner.predict_wind_direction(10, 290, predict_date_without_samples)
    precip_result = machine_learner.predict_precipitation(3, predict_date_without_samples)
    assert temp_result is None
    assert rh_result is None
    assert wdir_result is None
    assert precip_result is None
