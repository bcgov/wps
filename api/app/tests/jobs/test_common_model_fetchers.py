from datetime import datetime
import numpy
from app.jobs.common_model_fetchers import accumulate_nam_precipitation
from app.db.models.weather_models import ModelRunGridSubsetPrediction


ZERO_HOUR_TIMESTAMP = datetime(2023, 9, 7, 0, 0, 0)
TWELVE_HOUR_TIMESTAMP = datetime(2023, 9, 7, 12, 0, 0)
NON_ACCUMULATING_HOUR_TIMESTAMP = datetime(2023, 9, 7, 20, 0, 0)
MODEL_RUN_ZERO_HOUR = 0
MODEL_RUN_SIX_HOUR = 6
MODEL_RUN_TWELVE_HOUR = 12
MODEL_RUN_EIGHTEEN_HOUR = 18


def test_accumulator_is_zero_prediction_apcp_sfc_0_is_none():
    nam_cumulative_precip = numpy.array([0, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=None, prediction_timestamp=ZERO_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_ZERO_HOUR)
    assert (cumulative_precip == [0, 0, 0, 0]).all()
    assert (prediction_precip == [0, 0, 0, 0]).all()


def test_accumulator_has_value_prediction_apcp_sfc_0_is_none():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=None, prediction_timestamp=ZERO_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_ZERO_HOUR)
    assert (cumulative_precip == [1, 0, 0, 0]).all()
    assert (prediction_precip == [1, 0, 0, 0]).all()


def test_accumulator_has_value_prediction_apcp_sfc_0_is_zero():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[0, 0, 0, 0], prediction_timestamp=ZERO_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_ZERO_HOUR)
    assert (cumulative_precip == [1, 0, 0, 0]).all()
    assert (prediction_precip == [1, 0, 0, 0]).all()


def test_accumulator_has_value_prediction_apcp_sfc_0_has_value():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[1, 0, 0, 0], prediction_timestamp=ZERO_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_ZERO_HOUR)
    assert (cumulative_precip == [2, 0, 0, 0]).all()
    assert (prediction_precip == [2, 0, 0, 0]).all()


def test_zero_hour_timstamp_with_accumulating_hour_timestamp():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[1, 0, 0, 0], prediction_timestamp=NON_ACCUMULATING_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_ZERO_HOUR)
    assert (cumulative_precip == [1, 0, 0, 0]).all()
    assert (prediction_precip == [2, 0, 0, 0]).all()


def test_zero_hour_model_run_with_accumulating_timestamp():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[1, 0, 0, 0], prediction_timestamp=TWELVE_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_ZERO_HOUR)
    assert (cumulative_precip == [2, 0, 0, 0]).all()
    assert (prediction_precip == [2, 0, 0, 0]).all()


def test_zero_hour_model_run_with_non_accumulating_timestamp():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[1, 0, 0, 0], prediction_timestamp=NON_ACCUMULATING_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_ZERO_HOUR)
    assert (cumulative_precip == [1, 0, 0, 0]).all()
    assert (prediction_precip == [2, 0, 0, 0]).all()


def test_six_hour_model_run_with_accumulating_timestamp():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[1, 0, 0, 0], prediction_timestamp=TWELVE_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_SIX_HOUR)
    assert (cumulative_precip == [2, 0, 0, 0]).all()
    assert (prediction_precip == [2, 0, 0, 0]).all()


def test_six_hour_model_run_with_non_accumulating_timestamp():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[1, 0, 0, 0], prediction_timestamp=NON_ACCUMULATING_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_SIX_HOUR)
    assert (cumulative_precip == [1, 0, 0, 0]).all()
    assert (prediction_precip == [2, 0, 0, 0]).all()


def test_twelve_hour_model_run_with_accumulating_timestamp():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[1, 0, 0, 0], prediction_timestamp=TWELVE_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_TWELVE_HOUR)
    assert (cumulative_precip == [2, 0, 0, 0]).all()
    assert (prediction_precip == [2, 0, 0, 0]).all()


def test_twelve_hour_model_run_with_non_accumulating_timestamp():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[1, 0, 0, 0], prediction_timestamp=NON_ACCUMULATING_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_TWELVE_HOUR)
    assert (cumulative_precip == [1, 0, 0, 0]).all()
    assert (prediction_precip == [2, 0, 0, 0]).all()


def test_eighteen_hour_model_run_with_accumulating_timestamp():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[1, 0, 0, 0], prediction_timestamp=TWELVE_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_EIGHTEEN_HOUR)
    assert (cumulative_precip == [2, 0, 0, 0]).all()
    assert (prediction_precip == [2, 0, 0, 0]).all()


def test_eighteen_hour_model_run_with_non_accumulating_timestamp():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[1, 0, 0, 0], prediction_timestamp=NON_ACCUMULATING_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_EIGHTEEN_HOUR)
    assert (cumulative_precip == [1, 0, 0, 0]).all()
    assert (prediction_precip == [2, 0, 0, 0]).all()
