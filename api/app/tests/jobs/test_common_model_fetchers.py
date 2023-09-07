from datetime import datetime
import numpy
from app.jobs.common_model_fetchers import accumulate_nam_precipitation
from app.db.models.weather_models import ModelRunGridSubsetPrediction


zero_hour_timestamp = datetime(2023, 9, 7, 0, 0, 0)
six_hour_timestamp = datetime(2023, 9, 7, 6, 0, 0)
non_accumulating_hour_timestamp = datetime(2023, 9, 7, 20, 0, 0)


def test_accumulator_is_zero_prediction_apcp_sfc_0_is_none():
    nam_cumulative_precip = numpy.array([0, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=None, prediction_timestamp=zero_hour_timestamp)
    model_run_hour = 0
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, model_run_hour)
    assert (cumulative_precip == [0, 0, 0, 0]).all()
    assert (prediction_precip == [0, 0, 0, 0]).all()


def test_accumulator_has_value_prediction_apcp_sfc_0_is_none():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=None, prediction_timestamp=zero_hour_timestamp)
    model_run_hour = 0
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, model_run_hour)
    assert (cumulative_precip == [1, 0, 0, 0]).all()
    assert (prediction_precip == [1, 0, 0, 0]).all()


def test_accumulator_has_value_prediction_apcp_sfc_0_is_zero():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[0, 0, 0, 0], prediction_timestamp=zero_hour_timestamp)
    model_run_hour = 0
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, model_run_hour)
    assert (cumulative_precip == [1, 0, 0, 0]).all()
    assert (prediction_precip == [1, 0, 0, 0]).all()


def test_accumulator_has_value_prediction_apcp_sfc_0_has_value():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[1, 0, 0, 0], prediction_timestamp=zero_hour_timestamp)
    model_run_hour = 0
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, model_run_hour)
    assert (cumulative_precip == [2, 0, 0, 0]).all()
    assert (prediction_precip == [2, 0, 0, 0]).all()


def test_non_accumulating_prediction_hour():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[1, 0, 0, 0], prediction_timestamp=non_accumulating_hour_timestamp)
    model_run_hour = 0
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, model_run_hour)
    assert (cumulative_precip == [1, 0, 0, 0]).all()
    assert (prediction_precip == [2, 0, 0, 0]).all()
