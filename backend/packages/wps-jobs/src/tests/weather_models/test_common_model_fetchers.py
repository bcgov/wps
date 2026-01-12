from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import numpy
import pytest
from weather_model_jobs.common_model_fetchers import (
    ModelValueProcessor,
    accumulate_nam_precipitation,
)
from wps_shared.db.models.weather_models import ModelRunGridSubsetPrediction
from wps_shared.schemas.stations import WeatherStation

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
        apcp_sfc_0=None, prediction_timestamp=ZERO_HOUR_TIMESTAMP
    )
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_ZERO_HOUR
    )
    assert (cumulative_precip == [0, 0, 0, 0]).all()
    assert (prediction_precip == [0, 0, 0, 0]).all()


def test_accumulator_has_value_prediction_apcp_sfc_0_is_none():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=None, prediction_timestamp=ZERO_HOUR_TIMESTAMP
    )
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_ZERO_HOUR
    )
    assert (cumulative_precip == [1, 0, 0, 0]).all()
    assert (prediction_precip == [1, 0, 0, 0]).all()


def test_accumulator_has_value_prediction_apcp_sfc_0_is_zero():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[0, 0, 0, 0], prediction_timestamp=ZERO_HOUR_TIMESTAMP
    )
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_ZERO_HOUR
    )
    assert (cumulative_precip == [1, 0, 0, 0]).all()
    assert (prediction_precip == [1, 0, 0, 0]).all()


def test_accumulator_has_value_prediction_apcp_sfc_0_has_value():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[1, 0, 0, 0], prediction_timestamp=ZERO_HOUR_TIMESTAMP
    )
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_ZERO_HOUR
    )
    assert (cumulative_precip == [2, 0, 0, 0]).all()
    assert (prediction_precip == [2, 0, 0, 0]).all()


def test_zero_hour_timstamp_with_accumulating_hour_timestamp():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[1, 0, 0, 0], prediction_timestamp=NON_ACCUMULATING_HOUR_TIMESTAMP
    )
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_ZERO_HOUR
    )
    assert (cumulative_precip == [1, 0, 0, 0]).all()
    assert (prediction_precip == [2, 0, 0, 0]).all()


def test_zero_hour_model_run_with_accumulating_timestamp():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[1, 0, 0, 0], prediction_timestamp=TWELVE_HOUR_TIMESTAMP
    )
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_ZERO_HOUR
    )
    assert (cumulative_precip == [2, 0, 0, 0]).all()
    assert (prediction_precip == [2, 0, 0, 0]).all()


def test_zero_hour_model_run_with_non_accumulating_timestamp():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[1, 0, 0, 0], prediction_timestamp=NON_ACCUMULATING_HOUR_TIMESTAMP
    )
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_ZERO_HOUR
    )
    assert (cumulative_precip == [1, 0, 0, 0]).all()
    assert (prediction_precip == [2, 0, 0, 0]).all()


def test_six_hour_model_run_with_accumulating_timestamp():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[1, 0, 0, 0], prediction_timestamp=TWELVE_HOUR_TIMESTAMP
    )
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_SIX_HOUR
    )
    assert (cumulative_precip == [2, 0, 0, 0]).all()
    assert (prediction_precip == [2, 0, 0, 0]).all()


def test_six_hour_model_run_with_non_accumulating_timestamp():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[1, 0, 0, 0], prediction_timestamp=NON_ACCUMULATING_HOUR_TIMESTAMP
    )
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_SIX_HOUR
    )
    assert (cumulative_precip == [1, 0, 0, 0]).all()
    assert (prediction_precip == [2, 0, 0, 0]).all()


def test_twelve_hour_model_run_with_accumulating_timestamp():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[1, 0, 0, 0], prediction_timestamp=TWELVE_HOUR_TIMESTAMP
    )
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_TWELVE_HOUR
    )
    assert (cumulative_precip == [2, 0, 0, 0]).all()
    assert (prediction_precip == [2, 0, 0, 0]).all()


def test_twelve_hour_model_run_with_non_accumulating_timestamp():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[1, 0, 0, 0], prediction_timestamp=NON_ACCUMULATING_HOUR_TIMESTAMP
    )
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_TWELVE_HOUR
    )
    assert (cumulative_precip == [1, 0, 0, 0]).all()
    assert (prediction_precip == [2, 0, 0, 0]).all()


def test_eighteen_hour_model_run_with_accumulating_timestamp():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[1, 0, 0, 0], prediction_timestamp=TWELVE_HOUR_TIMESTAMP
    )
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_EIGHTEEN_HOUR
    )
    assert (cumulative_precip == [2, 0, 0, 0]).all()
    assert (prediction_precip == [2, 0, 0, 0]).all()


def test_eighteen_hour_model_run_with_non_accumulating_timestamp():
    nam_cumulative_precip = numpy.array([1, 0, 0, 0])
    prediction = ModelRunGridSubsetPrediction(
        apcp_sfc_0=[1, 0, 0, 0], prediction_timestamp=NON_ACCUMULATING_HOUR_TIMESTAMP
    )
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_EIGHTEEN_HOUR
    )
    assert (cumulative_precip == [1, 0, 0, 0]).all()
    assert (prediction_precip == [2, 0, 0, 0]).all()


@pytest.fixture
def mock_station():
    station = MagicMock(spec=WeatherStation)
    station.code = 1215
    station.lat = 50.0
    station.long = -120.0
    return station


@pytest.fixture
def mock_model_run():
    model_run = MagicMock()
    model_run.id = 42
    model_run.prediction_run_timestamp = datetime(2025, 6, 5, 6, 0, 0)
    return model_run


@pytest.fixture
def mock_machine():
    machine = MagicMock()
    return machine


@pytest.fixture
def mock_session():
    session = MagicMock()
    return session


@pytest.fixture
def processor(mock_session):
    # Patch get_stations_synchronously to avoid network calls during tests
    with patch(
        "weather_model_jobs.common_model_fetchers.get_stations_synchronously",
        return_value=[],
    ):
        return ModelValueProcessor(mock_session)


@pytest.fixture
def mock_prediction():
    prediction = MagicMock()
    prediction.id = 123
    prediction.prediction_timestamp = datetime(2025, 6, 5, 12, 0, 0)
    prediction.tmp_tgl_2 = 10.0
    prediction.rh_tgl_2 = 50.0
    prediction.apcp_sfc_0 = 2.0
    prediction.wind_tgl_10 = 5.0
    prediction.wdir_tgl_10 = 180.0
    return prediction


@pytest.fixture
def mock_station_prediction():
    station_prediction = MagicMock()
    station_prediction.apcp_sfc_0 = 1.0
    return station_prediction


@patch("weather_model_jobs.common_model_fetchers.get_weather_station_model_prediction")
@patch("weather_model_jobs.common_model_fetchers.WeatherStationModelPrediction")
@patch(
    "weather_model_jobs.common_model_fetchers.time_utils.get_utc_now",
    return_value=datetime(2025, 6, 5, 13, 0, 0),
)
@patch("weather_model_jobs.common_model_fetchers.get_accumulated_precipitation")
def test_process_prediction_populates_fields_and_accumulates_correct_precip(
    mock_get_accumulated_precipitation,
    mock_get_utc_now,
    weather_station_model_prediction_mock,
    mock_get_weather_station_model_prediction,
    processor,
    mock_prediction,
    mock_station,
    mock_model_run,
    mock_machine,
    mock_session,
):
    # Simulate no existing prediction
    mock_get_weather_station_model_prediction.return_value = None
    mock_station_prediction = MagicMock()
    weather_station_model_prediction_mock.return_value = mock_station_prediction

    processor._calculate_delta_precip = MagicMock(return_value=1.5)
    processor._add_bias_adjustments_to_prediction = MagicMock()
    processor._add_interpolated_bias_adjustments_to_prediction = MagicMock()

    processor._process_prediction(
        mock_prediction,
        mock_station,
        mock_model_run,
        mock_machine,
        prediction_is_interpolated=False,
    )

    # Should create a new WeatherStationModelPrediction
    weather_station_model_prediction_mock.assert_called_once()
    # Should set fields
    assert mock_station_prediction.station_code == mock_station.code
    assert mock_station_prediction.prediction_model_run_timestamp_id == mock_model_run.id
    assert mock_station_prediction.prediction_timestamp == mock_prediction.prediction_timestamp
    assert mock_station_prediction.tmp_tgl_2 == pytest.approx(10.0)
    assert mock_station_prediction.rh_tgl_2 == pytest.approx(50.0)
    assert mock_station_prediction.apcp_sfc_0 == pytest.approx(2.0)
    assert mock_station_prediction.wind_tgl_10 == pytest.approx(5.0)
    assert mock_station_prediction.wdir_tgl_10 == pytest.approx(180.0)
    assert mock_station_prediction.delta_precip == pytest.approx(1.5)
    assert mock_station_prediction.update_date == datetime(2025, 6, 5, 13, 0, 0)
    # Should call add_bias_adjustments_to_prediction
    processor._add_bias_adjustments_to_prediction.assert_called_once_with(
        mock_station_prediction, mock_machine
    )
    start_date = mock_prediction.prediction_timestamp - timedelta(hours=24)
    called_session, called_station_code, called_start_date, called_end_date = (
        mock_get_accumulated_precipitation.call_args[0]
    )

    # Should call get_accumulated_precipitation with correct parameters
    assert called_session == mock_session
    assert called_station_code == mock_station.code
    assert called_start_date == start_date
    assert called_end_date == mock_model_run.prediction_run_timestamp

    # Should add to session
    mock_session.add.assert_called_with(mock_station_prediction)


@patch("weather_model_jobs.common_model_fetchers.get_weather_station_model_prediction")
@patch(
    "weather_model_jobs.common_model_fetchers.time_utils.get_utc_now",
    return_value=datetime(2023, 9, 7, 13, 0, 0),
)
def test_process_prediction_existing_prediction_is_updated(
    mock_get_utc_now,
    mock_get_weather_station_model_prediction,
    processor,
    mock_prediction,
    mock_station,
    mock_model_run,
    mock_machine,
    mock_session,
):
    # Simulate existing prediction
    existing_prediction = MagicMock()
    mock_get_weather_station_model_prediction.return_value = existing_prediction

    processor._calculate_past_24_hour_precip = MagicMock(return_value=5.0)
    processor._calculate_delta_precip = MagicMock(return_value=2.0)
    processor._add_bias_adjustments_to_prediction = MagicMock()

    processor._process_prediction(
        mock_prediction,
        mock_station,
        mock_model_run,
        mock_machine,
        prediction_is_interpolated=False,
    )

    # Should not create a new WeatherStationModelPrediction
    # Should update the existing one
    assert existing_prediction.station_code == mock_station.code
    assert existing_prediction.prediction_model_run_timestamp_id == mock_model_run.id
    assert existing_prediction.prediction_timestamp == mock_prediction.prediction_timestamp
    assert existing_prediction.tmp_tgl_2 == pytest.approx(10.0)
    assert existing_prediction.rh_tgl_2 == pytest.approx(50.0)
    assert existing_prediction.apcp_sfc_0 == pytest.approx(2.0)
    assert existing_prediction.wind_tgl_10 == pytest.approx(5.0)
    assert existing_prediction.wdir_tgl_10 == pytest.approx(180.0)
    assert existing_prediction.precip_24h == pytest.approx(5.0)
    assert existing_prediction.delta_precip == pytest.approx(2.0)
    assert existing_prediction.update_date == datetime(2023, 9, 7, 13, 0, 0)
    mock_session.add.assert_called_with(existing_prediction)
