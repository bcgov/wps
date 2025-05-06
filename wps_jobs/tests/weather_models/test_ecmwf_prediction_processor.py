import pytest
from unittest.mock import MagicMock, create_autospec
from datetime import datetime, timedelta, timezone

from pytest_mock import MockerFixture
from wps_jobs.weather_model_jobs import ModelEnum
from wps_jobs.weather_model_jobs.ecmwf_prediction_processor import ECMWFPredictionProcessor
from wps_shared.schemas.stations import WeatherStation
from wps_shared.db.crud.model_run_repository import ModelRunRepository
from wps_jobs.weather_model_jobs.machine_learning import StationMachineLearning
from wps_shared.db.models.weather_models import ModelRunPrediction, PredictionModelRunTimestamp

@pytest.fixture
def setup_processor():
    stations = [
        WeatherStation(code=1, long=10.0, lat=50.0, name="Station 1"),
        WeatherStation(code=1, long=20.0, lat=60.0, name="Station 2"),
    ]
    model_run_repository = MagicMock(spec=ModelRunRepository)
    prediction_run = MagicMock(spec=PredictionModelRunTimestamp)
    model_run_repository.session = MagicMock()
    machine = MagicMock(spec=StationMachineLearning)
    processor = ECMWFPredictionProcessor(stations, model_run_repository, prediction_run, machine)
    return processor, model_run_repository, prediction_run, machine

@pytest.fixture
def mock_predictions():
    processor = ECMWFPredictionProcessor([], None, None, None)
    prev_prediction = MagicMock(spec=ModelRunPrediction)
    prediction = MagicMock(spec=ModelRunPrediction)
    return processor, prev_prediction, prediction


@pytest.fixture
def mock_model_run_data():
    station = WeatherStation(code=1, long=10.0, lat=50.0, name="Station 1")
    model_run = MagicMock(spec=PredictionModelRunTimestamp)
    model_run.id = 123
    prediction = MagicMock(spec=ModelRunPrediction)
    prediction.prediction_timestamp = datetime(2023, 10, 2, 12, 0)
    station_prediction = MagicMock()
    station_prediction.prediction_timestamp = datetime(2023, 10, 2, 12, 0)
    station_prediction.apcp_sfc_0 = 10.0
    return station, model_run, prediction, station_prediction


def test_process_model_run_for_station(setup_processor):
    processor, model_run_repository, _, __ = setup_processor

    # Mock data
    station = WeatherStation(code=1, long=10.0, lat=50.0, name="Station 1")
    model_run = create_autospec(PredictionModelRunTimestamp)
    model_run_predictions = [
        ModelRunPrediction(prediction_timestamp=datetime(2023, 10, 1, 18, 0)),
        ModelRunPrediction(prediction_timestamp=datetime(2023, 10, 1, 21, 0)),
    ]
    model_run_repository.get_model_run_predictions_for_station.return_value = model_run_predictions

    # Mock methods
    processor._should_interpolate = MagicMock(return_value=True)
    processor._process_prediction = MagicMock()

    # Call the method
    processor._process_model_run_for_station(model_run, station)

    # Assertions
    model_run_repository.get_model_run_predictions_for_station.assert_called_once_with(station.code, model_run)
    processor._should_interpolate.assert_called()
    assert processor._process_prediction.call_count == 3  # Two predictions + one interpolated


@pytest.mark.parametrize(
    "prev_timestamp, next_timestamp, expected",
    [
        # timestamps on the same day surrounding 20:00 UTC
        (datetime(2023, 10, 1, 18, 0), datetime(2023, 10, 1, 21, 0), True),
        # timestamps on the same day but not surrounding 20:00 UTC
        (datetime(2023, 10, 1, 10, 0), datetime(2023, 10, 1, 15, 0), False),
        # timestamps on different days
        (datetime(2023, 10, 1, 23, 0), datetime(2023, 10, 2, 1, 0), True),
    ],
)
def test_should_interpolate(prev_timestamp, next_timestamp, expected, mock_predictions):
    processor, prev_prediction, prediction = mock_predictions
    prev_prediction.prediction_timestamp = prev_timestamp
    prediction.prediction_timestamp = next_timestamp

    result = processor._should_interpolate(prev_prediction, prediction)
    assert result is expected

def test_should_interpolate_assertion_error(mock_predictions):
    processor, prev_prediction, prediction = mock_predictions

    # Mock timestamps where next timestamp is earlier than previous timestamp
    prev_prediction.prediction_timestamp = datetime(2023, 10, 2, 1, 0)
    prediction.prediction_timestamp = datetime(2023, 10, 1, 23, 0)

    with pytest.raises(AssertionError, match="Next timestamp must be greater than previous timestamp"):
        processor._should_interpolate(prev_prediction, prediction)
    
def test_weather_station_prediction_initializer(setup_processor, mocker: MockerFixture):
    processor, model_run_repository, _, _ = setup_processor

    # Mock data
    station = WeatherStation(code=1, long=10.0, lat=50.0, name="Station 1")
    model_run = MagicMock(spec=PredictionModelRunTimestamp)
    model_run.id = 123
    model_run.prediction_run_timestamp = datetime(2023, 10, 1, 12, 0)
    prediction = MagicMock(spec=ModelRunPrediction)
    prediction.prediction_timestamp = datetime(2023, 10, 1, 12, 0)

    # Mock repository behavior
    model_run_repository.get_weather_station_model_prediction.return_value = None

    # Call the method
    station_prediction = processor._weather_station_prediction_initializer(station, model_run, prediction)

    # Assertions
    model_run_repository.get_weather_station_model_prediction.assert_called_once_with(
        station.code, model_run.id, prediction.prediction_timestamp
    )
    assert station_prediction.station_code == station.code
    assert station_prediction.prediction_model_run_timestamp_id == model_run.id
    assert station_prediction.prediction_timestamp == model_run.prediction_run_timestamp
    
def test_interpolate_20_00_values_valid_interpolation(mock_predictions, mocker: MockerFixture):
    processor, _, _ = mock_predictions

    # Mock data
    prev_datetime = datetime(2023, 10, 1, 18, 0)
    next_datetime = datetime(2023, 10, 1, 21, 0)
    target_datetime = datetime(2023, 10, 1, 20, 0)
    prev_value = 10.0
    next_value = 20.0

    result = processor.interpolate_20_00_values(prev_datetime, next_datetime, prev_value, next_value, target_datetime)

    assert result == pytest.approx(16.666, rel=0.1)



@pytest.mark.parametrize(
    "prev_timestamp, next_timestamp, target_timestamp, expected",
    [
        (datetime(2023, 10, 1, 18, 0), datetime(2023, 10, 1, 19, 0), datetime(2023, 10, 1, 20, 0), "Next datetime must be after target datetime"),
        (datetime(2023, 10, 1, 21, 0), datetime(2023, 10, 1, 22, 0), datetime(2023, 10, 1, 20, 0), "Previous datetime must be before target datetime"),
        (datetime(2023, 10, 1, 18, 0), datetime(2023, 10, 1, 21, 0), datetime(2023, 10, 1, 19, 0), "Target datetime must be at 20:00 UTC"),
    ],
)
def test_interpolate_20_00_values_invalid_timestamps(prev_timestamp, next_timestamp, target_timestamp, expected, mock_predictions):
    processor, _, _ = mock_predictions
    prev_value = 10.0
    next_value = 20.0

    # Call the method and assert exception
    with pytest.raises(AssertionError, match=expected):
        processor.interpolate_20_00_values(prev_timestamp, next_timestamp, prev_value, next_value, target_timestamp)

def test_calculate_past_24_hour_precip_with_previous_prediction(setup_processor, mock_model_run_data):
    processor, model_run_repository, _, _ = setup_processor
    station, model_run, prediction, station_prediction = mock_model_run_data

    # Mock repository behavior
    previous_prediction = MagicMock()
    previous_prediction.apcp_sfc_0 = 5.0
    model_run_repository.get_weather_station_model_prediction.return_value = previous_prediction

    # Call the method
    result = processor._calculate_past_24_hour_precip(station, model_run, prediction, station_prediction)

    # Assertions
    model_run_repository.get_weather_station_model_prediction.assert_called_once_with(
        station.code, model_run.id, prediction.prediction_timestamp - timedelta(days=1)
    )
    assert result == 5.0


def test_calculate_past_24_hour_precip_without_previous_prediction(setup_processor, mock_model_run_data):
    processor, model_run_repository, _, _ = setup_processor
    station, model_run, prediction, station_prediction = mock_model_run_data

    # Mock repository behavior
    model_run_repository.get_weather_station_model_prediction.return_value = None
    model_run_repository.get_accumulated_precipitation.return_value = 3.0

    # Call the method
    result = processor._calculate_past_24_hour_precip(station, model_run, prediction, station_prediction)

    # Assertions
    model_run_repository.get_weather_station_model_prediction.assert_called_once_with(
        station.code, model_run.id, prediction.prediction_timestamp - timedelta(days=1)
    )
    model_run_repository.get_accumulated_precipitation.assert_called_once_with(
        station.code,
        prediction.prediction_timestamp - timedelta(days=1),
        datetime(year=2023, month=10, day=2, tzinfo=timezone.utc),
    )
    assert result == 13.0



@pytest.mark.parametrize(
    "prev_prediction, station_value, expected",
    [
        # without previous prediction
        (None, 10.0, 10.0),
        # with previous prediction
        (5.0, 10.0, 5.0),
    ],
)
def test_calculate_delta_precip(prev_prediction, station_value, expected, setup_processor, mock_model_run_data):
    processor, _, _, _ = setup_processor
    _, _, _, station_prediction = mock_model_run_data

    def setup_prev_prediction():
        if prev_prediction is None:
            return None
        
        prev_prediction_mock = MagicMock()
        prev_prediction_mock.apcp_sfc_0 = prev_prediction
        return prev_prediction_mock

    # No previous prediction
    prev_prediction = setup_prev_prediction()
    station_prediction.apcp_sfc_0 = station_value

    # Call the method
    result = processor._calculate_delta_precip(prev_prediction, station_prediction)

    # Assertions
    assert result == expected

@pytest.fixture()
def mock_process_data(setup_processor, mock_model_run_data):
    processor, model_run_repository, _, machine = setup_processor
    station, model_run, prediction, station_prediction = mock_model_run_data
    
    station_prediction = MagicMock()
    station_prediction.prediction_timestamp = datetime(2023, 10, 1, 12, 0)
    station_prediction.tmp_tgl_2 = 15.0
    station_prediction.rh_tgl_2 = 50.0
    station_prediction.wind_tgl_10 = 5.0
    station_prediction.wdir_tgl_10 = 180.0
    station_prediction.precip_24h = 10.0

    # Mock methods
    processor._weather_station_prediction_initializer = MagicMock(return_value=station_prediction)
    processor._calculate_past_24_hour_precip = MagicMock(return_value=10.0)
    processor._calculate_delta_precip = MagicMock(return_value=5.0)
    machine.predict_temperature = MagicMock(return_value=14.0)
    machine.predict_rh = MagicMock(return_value=45.0)
    machine.predict_wind_speed = MagicMock(return_value=4.0)
    machine.predict_wind_direction = MagicMock(return_value=170.0)
    machine.predict_precipitation = MagicMock(return_value=8.0)

    return processor, model_run_repository, machine, station_prediction, station, model_run, prediction

def test_process_prediction_with_interpolation(mock_process_data):
    processor, model_run_repository, machine, station_prediction, station, model_run, prediction = mock_process_data

    prev_prediction = MagicMock(spec=ModelRunPrediction)
    prev_prediction.prediction_timestamp = datetime(2023, 10, 1, 18, 0)
    prediction.prediction_timestamp = datetime(2023, 10, 1, 21, 0)
    processor.interpolate_20_00_values = MagicMock(return_value=12.5)

    processor._process_prediction(prev_prediction, prediction, station, model_run, machine, prediction_is_interpolated=True)

    processor._weather_station_prediction_initializer.assert_called_once_with(station, model_run, prediction)
    processor._calculate_past_24_hour_precip.assert_called_once_with(station, model_run, prediction, station_prediction)
    processor._calculate_delta_precip.assert_called_once_with(prev_prediction, station_prediction)
    processor.interpolate_20_00_values.assert_called()
    machine.predict_temperature.assert_called()
    machine.predict_rh.assert_called()
    machine.predict_wind_speed.assert_called()
    machine.predict_wind_direction.assert_called()
    machine.predict_precipitation.assert_called_once_with(station_prediction.precip_24h, station_prediction.prediction_timestamp)
    model_run_repository.store_weather_station_model_prediction.assert_called_once_with(station_prediction)


def test_process_prediction_without_interpolation(mock_process_data):
    processor, model_run_repository, machine, station_prediction, station, model_run, prediction = mock_process_data

    # Mock data
    prediction.prediction_timestamp = datetime(2023, 10, 1, 12, 0)

    # Call the method
    processor._process_prediction(None, prediction, station, model_run, machine, prediction_is_interpolated=False)

    # Assertions
    processor._weather_station_prediction_initializer.assert_called_once_with(station, model_run, prediction)
    processor._calculate_past_24_hour_precip.assert_called_once_with(station, model_run, prediction, station_prediction)
    processor._calculate_delta_precip.assert_called_once_with(None, station_prediction)
    machine.predict_temperature.assert_called_once_with(station_prediction.tmp_tgl_2, station_prediction.prediction_timestamp)
    machine.predict_rh.assert_called_once_with(station_prediction.rh_tgl_2, station_prediction.prediction_timestamp)
    machine.predict_wind_speed.assert_called_once_with(station_prediction.wind_tgl_10, station_prediction.prediction_timestamp)
    machine.predict_wind_direction.assert_called_once_with(station_prediction.wind_tgl_10, station_prediction.wdir_tgl_10, station_prediction.prediction_timestamp)
    machine.predict_precipitation.assert_called_once_with(station_prediction.precip_24h, station_prediction.prediction_timestamp)
    model_run_repository.store_weather_station_model_prediction.assert_called_once_with(station_prediction)

def test_process(setup_processor):
    processor, model_run_repository, _, _ = setup_processor

    # Mock data
    model_run = MagicMock()
    model = MagicMock()
    model_run_repository.get_prediction_model_run_timestamp_records.return_value = [(model_run, model)]

    processor._process_model_run = MagicMock()
    model_run_repository.mark_model_run_interpolated = MagicMock()

    # Call the method
    processor.process()

    # Assertions
    model_run_repository.get_prediction_model_run_timestamp_records.assert_called_once_with(
        complete=True, interpolated=False, model_type=ModelEnum.ECMWF
    )
    processor._process_model_run.assert_called_once_with(model_run)
    model_run_repository.mark_model_run_interpolated.assert_called_once_with(model_run)

def test_process_model_run(setup_processor):
    processor, _, _, _ = setup_processor

    # Mock data
    model_run = MagicMock(spec=PredictionModelRunTimestamp)
    model_run.id = 123
    stations = [
        WeatherStation(code=1, long=10.0, lat=50.0, name="Station 1"),
        WeatherStation(code=2, long=20.0, lat=60.0, name="Station 2"),
    ]
    processor.stations = stations

    # Mock methods
    processor._process_model_run_for_station = MagicMock()

    # Call the method
    processor._process_model_run(model_run)

    # Assertions
    assert processor._process_model_run_for_station.call_count == len(stations)
    for _, station in enumerate(stations):
        processor._process_model_run_for_station.assert_any_call(model_run, station)
        





