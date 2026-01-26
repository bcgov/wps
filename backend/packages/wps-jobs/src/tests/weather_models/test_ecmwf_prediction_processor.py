from datetime import datetime, timedelta, timezone
import math
from unittest.mock import MagicMock, call

import pytest
import weather_model_jobs.ecmwf_prediction_processor
from pytest_mock import MockerFixture
from weather_model_jobs import ModelEnum
from weather_model_jobs.ecmwf_prediction_processor import ECMWFPredictionProcessor
from wps_shared.db.crud.model_run_repository import ModelRunRepository
from wps_shared.db.models.weather_models import (
    ModelRunPrediction,
    PredictionModelRunTimestamp,
    WeatherStationModelPrediction,
)
from wps_shared.schemas.stations import WeatherStation


@pytest.fixture
def setup_processor():
    stations = [
        WeatherStation(code=1, long=10.0, lat=50.0, name="Station 1"),
        WeatherStation(code=1, long=20.0, lat=60.0, name="Station 2"),
    ]
    model_run_repository = MagicMock(spec=ModelRunRepository)
    model_run_repository.session = MagicMock()
    processor = ECMWFPredictionProcessor(stations, model_run_repository)
    return processor, model_run_repository


@pytest.fixture
def mock_predictions():
    processor = ECMWFPredictionProcessor([], None)
    prev_prediction = MagicMock(spec=ModelRunPrediction)
    prediction = MagicMock(spec=ModelRunPrediction)
    return processor, prev_prediction, prediction


@pytest.fixture
def mock_model_run_data():
    station = WeatherStation(code=1, long=10.0, lat=50.0, name="Station 1")
    model_run = MagicMock(spec=PredictionModelRunTimestamp)
    model_run.id = 123
    model_run.prediction_run_timestamp = datetime(2023, 10, 2, 11, 0)
    prediction = MagicMock(spec=ModelRunPrediction)
    prediction.prediction_timestamp = datetime(2023, 10, 2, 12, 0)
    station_prediction = MagicMock()
    station_prediction.prediction_timestamp = datetime(2023, 10, 2, 12, 0)
    station_prediction.apcp_sfc_0 = 0.0
    return station, model_run, prediction, station_prediction


def test_process_model_run_for_station(setup_processor, mocker: MockerFixture):
    """
    Test the `_process_model_run_for_station` method of the processor.

    This test verifies that the processor correctly handles the processing of
    model run predictions for a given weather station, including applying bias
    adjustments and interpolated bias adjustments.
    """
    processor, model_run_repository = setup_processor

    # Mock data
    station = WeatherStation(code=1, long=10.0, lat=50.0, name="Station 1")
    model_run = MagicMock(spec=PredictionModelRunTimestamp)
    model_run_predictions = [
        ModelRunPrediction(prediction_timestamp=datetime(2023, 10, 1, 18, 0), apcp_sfc_0=0.0),
        ModelRunPrediction(prediction_timestamp=datetime(2023, 10, 1, 21, 0), apcp_sfc_0=0.0),
    ]
    interpolated_noon_prediction_spy = mocker.spy(
        weather_model_jobs.ecmwf_prediction_processor,
        "construct_interpolated_noon_prediction",
    )
    initialize_station_prediction_spy = mocker.spy(processor, "initialize_station_prediction")
    model_run_repository.get_model_run_predictions_for_station.return_value = model_run_predictions

    # Mock methods
    processor._apply_bias_adjustments = MagicMock()
    processor._apply_interpolated_bias_adjustments = MagicMock()

    # Call the method
    processor._process_model_run_for_station(model_run, station)

    # Assertions
    model_run_repository.get_model_run_predictions_for_station.assert_called_once_with(
        station.code, model_run
    )
    # This should be called for both predictions, 18:00 UTC and 21:00 UTC
    assert processor._apply_bias_adjustments.call_count == 2
    # This is called the 2nd iteration where the previous prediction is for 18:00 UTC and the next prediction is for 21:00 UTC
    assert processor._apply_interpolated_bias_adjustments.call_count == 1
    # This is called to create the interpolated noon prediction between 18:00 UTC and 21:00 UTC
    assert interpolated_noon_prediction_spy.call_count == 1
    # 1st call to initialize_station_prediction does not construct the noon prediction
    assert initialize_station_prediction_spy.call_args_list[0][0][0] is None
    assert initialize_station_prediction_spy.call_args_list[0][0][1] == model_run_predictions[0]
    # 2nd call to initialize_station_prediction constructs the noon prediction, and does not use prev or next prediction
    assert initialize_station_prediction_spy.call_args_list[1][0][1] != model_run_predictions[0]
    assert initialize_station_prediction_spy.call_args_list[1][0][1] != model_run_predictions[1]


@pytest.mark.parametrize(
    "prev_timestamp, next_timestamp, expected",
    [
        # timestamps on the same day surrounding 20:00 UTC
        (
            datetime(2023, 10, 1, 18, 0, tzinfo=timezone.utc),
            datetime(2023, 10, 1, 21, 0, tzinfo=timezone.utc),
            True,
        ),
        # timestamps on the same day but not surrounding 20:00 UTC
        (
            datetime(2023, 10, 1, 10, 0, tzinfo=timezone.utc),
            datetime(2023, 10, 1, 15, 0, tzinfo=timezone.utc),
            False,
        ),
        # timestamps on different days, later timestamp earlier than 21:00 UTC
        (
            datetime(2023, 10, 1, 21, 0, tzinfo=timezone.utc),
            datetime(2023, 10, 2, 0, 0, tzinfo=timezone.utc),
            False,
        ),
        # 18:00 UTC and 00:00 UTC on subsequent days should return true
        (
            datetime(2023, 10, 1, 18, 0, tzinfo=timezone.utc),
            datetime(2023, 10, 2, 00, 0, tzinfo=timezone.utc),
            True,
        ),
    ],
)
def test_should_interpolate(prev_timestamp, next_timestamp, expected, mock_predictions):
    """
    Test the `_should_interpolate` method of the processor.

    This test verifies whether the `_should_interpolate` method correctly determines
    if interpolation should occur between two prediction timestamps.
    """
    processor, prev_prediction, prediction = mock_predictions
    prev_prediction.prediction_timestamp = prev_timestamp
    prediction.prediction_timestamp = next_timestamp

    result = processor._should_interpolate(prev_prediction, prediction)
    assert result is expected


@pytest.mark.parametrize(
    "prev_timestamp, next_timestamp, expected",
    [
        # previous timestamp is later than next timestamp
        (
            datetime(2023, 10, 2, 1, 0, tzinfo=timezone.utc),
            datetime(2023, 10, 1, 23, 0, tzinfo=timezone.utc),
            "Next timestamp must be greater than previous timestamp",
        ),
        # timestamps greater than 24 hours apart
        (
            datetime(2023, 10, 1, 21, 0, tzinfo=timezone.utc),
            datetime(2023, 10, 2, 22, 0, tzinfo=timezone.utc),
            "Timestamps must be no more than 24 hours apart",
        ),
    ],
)
def test_should_interpolate_assertion_error(
    prev_timestamp, next_timestamp, expected, mock_predictions
):
    """
    Test the `_should_interpolate` method to ensure it raises an `AssertionError`
    when the `prediction_timestamp` of the next prediction is earlier than the
    `prediction_timestamp` of the previous prediction.

    This test verifies that the method enforces the assumption that the next
    timestamp must always be greater than the previous timestamp.
    """
    processor, prev_prediction, prediction = mock_predictions

    # Mock timestamps where next timestamp is earlier than previous timestamp
    prev_prediction.prediction_timestamp = prev_timestamp
    prediction.prediction_timestamp = next_timestamp

    with pytest.raises(AssertionError, match=expected):
        processor._should_interpolate(prev_prediction, prediction)


@pytest.mark.parametrize(
    "existing_station_model_prediction, prediction_timestamp",
    [
        # existing station model prediction
        (
            WeatherStationModelPrediction(
                station_code=123,
                prediction_model_run_timestamp_id=123,
                prediction_timestamp=datetime(2023, 10, 1, 12, 0),
                tmp_tgl_2=1,
                rh_tgl_2=1,
                apcp_sfc_0=1,
                wdir_tgl_10=1,
                wind_tgl_10=1,
                create_date=datetime(2023, 10, 1, 12, 0),
                update_date=datetime(2023, 10, 1, 12, 0) + timedelta(days=1),
            ),
            datetime(2023, 10, 1, 12, 0),
        ),
        # no existing station model prediction
        (None, datetime(2023, 10, 1, 12, 0)),
    ],
)
def test_weather_station_prediction_initializer(
    existing_station_model_prediction, prediction_timestamp, setup_processor
):
    """
    Test the `_weather_station_prediction_initializer` method of the processor.

    This test verifies the behavior of the `_weather_station_prediction_initializer` method
    when initializing a weather station prediction. It ensures that the method correctly
    retrieves or initializes a prediction object for a given weather station, model run,
    and prediction timestamp.
    """
    processor, model_run_repository = setup_processor

    # Mock data
    station = WeatherStation(code=123, long=10.0, lat=50.0, name="Station 1")
    model_run = MagicMock(spec=PredictionModelRunTimestamp)
    model_run.id = 123
    model_run.prediction_run_timestamp = datetime(2023, 10, 1, 12, 0)
    prediction = MagicMock(spec=ModelRunPrediction)
    prediction.prediction_timestamp = prediction_timestamp
    prediction.station_code = station.code
    prediction.prediction_model_run_timestamp_id = model_run.id

    # Mock repository behavior
    model_run_repository.get_weather_station_model_prediction.return_value = (
        existing_station_model_prediction
    )

    # Call the method
    station_prediction = processor._weather_station_prediction_initializer(prediction)

    # Assertions
    model_run_repository.get_weather_station_model_prediction.assert_called_once_with(
        prediction.station_code,
        prediction.prediction_model_run_timestamp_id,
        prediction.prediction_timestamp,
    )
    assert station_prediction.station_code == prediction.station_code
    assert (
        station_prediction.prediction_model_run_timestamp_id
        == prediction.prediction_model_run_timestamp_id
    )
    assert station_prediction.prediction_timestamp == prediction.prediction_timestamp
    if existing_station_model_prediction is not None:
        assert station_prediction.tmp_tgl_2 == existing_station_model_prediction.tmp_tgl_2
        assert station_prediction.rh_tgl_2 == existing_station_model_prediction.rh_tgl_2
        assert station_prediction.apcp_sfc_0 == existing_station_model_prediction.apcp_sfc_0
        assert station_prediction.wdir_tgl_10 == existing_station_model_prediction.wdir_tgl_10
        assert station_prediction.wind_tgl_10 == existing_station_model_prediction.wind_tgl_10
        assert station_prediction.update_date == existing_station_model_prediction.update_date
    else:
        assert station_prediction.update_date is None


def test_interpolate_20_00_values_valid_interpolation(mock_predictions):
    """
    Test the `interpolate_20_00_values` method of the processor for valid interpolation.

    This test verifies that the interpolation logic correctly calculates the value
    at a target datetime (20:00) based on the provided previous and next datetime-value pairs.
    """
    processor, _, _ = mock_predictions

    # Mock data
    prev_datetime = datetime(2023, 10, 1, 18, 0)
    next_datetime = datetime(2023, 10, 1, 21, 0)
    target_datetime = datetime(2023, 10, 1, 20, 0)
    prev_value = 10.0
    next_value = 20.0

    result = processor.interpolate_20_00_values(
        prev_datetime, next_datetime, prev_value, next_value, target_datetime
    )

    assert result == pytest.approx(16.666, rel=0.1)


@pytest.mark.parametrize(
    "prev_timestamp, next_timestamp, target_timestamp, expected",
    [
        (
            datetime(2023, 10, 1, 18, 0),
            datetime(2023, 10, 1, 19, 0),
            datetime(2023, 10, 1, 20, 0),
            "Next datetime must be after target datetime",
        ),
        (
            datetime(2023, 10, 1, 21, 0),
            datetime(2023, 10, 1, 22, 0),
            datetime(2023, 10, 1, 20, 0),
            "Previous datetime must be before target datetime",
        ),
        (
            datetime(2023, 10, 1, 18, 0),
            datetime(2023, 10, 1, 21, 0),
            datetime(2023, 10, 1, 19, 0),
            "Target datetime must be at 20:00 UTC",
        ),
    ],
)
def test_interpolate_20_00_values_invalid_timestamps(
    prev_timestamp, next_timestamp, target_timestamp, expected, mock_predictions
):
    """
    Test the `interpolate_20_00_values` method for invalid timestamp scenarios.

    This test ensures that the method raises an `AssertionError` with the correct
    error message when the provided timestamps do not meet the required conditions.
    """
    processor, _, _ = mock_predictions
    prev_value = 10.0
    next_value = 20.0

    # Call the method and assert exception
    with pytest.raises(AssertionError, match=expected):
        processor.interpolate_20_00_values(
            prev_timestamp, next_timestamp, prev_value, next_value, target_timestamp
        )


def test_calculate_past_24_hour_precip_with_previous_prediction(
    setup_processor, mock_model_run_data
):
    """
    Test the `_calculate_past_24_hour_precip` method of the processor.

    This test verifies that the method correctly calculates the past 24-hour
    precipitation using a previous prediction retrieved from the model run
    repository. It ensures that the repository is queried with the correct
    parameters and that the method returns the expected precipitation value.
    """
    processor, model_run_repository = setup_processor
    _, model_run, prediction, station_prediction = mock_model_run_data

    # Mock repository behavior
    previous_prediction = MagicMock()
    previous_prediction.apcp_sfc_0 = 5.0
    model_run_repository.get_weather_station_model_prediction.return_value = previous_prediction

    # Call the method
    result = processor._calculate_past_24_hour_precip(prediction, station_prediction, model_run)

    # Assertions
    model_run_repository.get_weather_station_model_prediction.assert_called_once_with(
        prediction.station_code,
        prediction.prediction_model_run_timestamp_id,
        prediction.prediction_timestamp - timedelta(days=1),
    )
    assert math.isclose(result, 5.0)


def test_calculate_past_24_hour_precip_without_previous_prediction(
    setup_processor, mock_model_run_data
):
    """
    Test the `_calculate_past_24_hour_precip` method when there is no previous prediction.

    This test verifies that the method correctly calculates the past 24-hour precipitation
    when no previous weather station model prediction exists in the repository.
    """
    processor, model_run_repository = setup_processor
    _, model_run, prediction, station_prediction = mock_model_run_data

    # Mock repository behavior
    model_run_repository.get_weather_station_model_prediction.return_value = None
    model_run_repository.get_accumulated_precipitation.return_value = 3.0

    # Call the method
    result = processor._calculate_past_24_hour_precip(prediction, station_prediction, model_run)

    # Assertions
    model_run_repository.get_weather_station_model_prediction.assert_called_once_with(
        prediction.station_code,
        prediction.prediction_model_run_timestamp_id,
        prediction.prediction_timestamp - timedelta(days=1),
    )
    model_run_repository.get_accumulated_precipitation.assert_called_once_with(
        prediction.station_code,
        prediction.prediction_timestamp - timedelta(days=1),
        model_run.prediction_run_timestamp,
    )
    assert math.isclose(result, 3.0)


@pytest.mark.parametrize(
    "prev_prediction, station_value, expected",
    [
        # without previous prediction
        (None, 10.0, 10.0),
        # with previous prediction
        (5.0, 10.0, 5.0),
    ],
)
def test_calculate_delta_precip(
    prev_prediction, station_value, expected, setup_processor, mock_model_run_data
):
    """
    Test the `_calculate_delta_precip` method of the processor.
    This test verifies that the `_calculate_delta_precip` method correctly calculates
    the delta precipitation value based on the previous prediction and the current
    station prediction.
    """
    processor, _ = setup_processor
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


def test_process(setup_processor):
    """
    Test the `process` method of the ECMWF prediction processor.

    This test verifies that the `process` method:
    1. Retrieves prediction model run timestamp records from the repository.
    2. Processes each model run using the `_process_model_run` method.
    3. Marks the processed model run as interpolated in the repository.
    """
    processor, model_run_repository = setup_processor

    # Mock data
    model_run = MagicMock()
    model = MagicMock()
    model_run_repository.get_prediction_model_run_timestamp_records.return_value = [
        (model_run, model)
    ]

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
    """
    Test the `_process_model_run` method of the processor.

    This test verifies that the `_process_model_run` method correctly processes
    a model run for all weather stations associated with the processor. It mocks
    the necessary data and methods to ensure the method behaves as expected.
    """
    processor, _ = setup_processor

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


def test_initialize_station_prediction(setup_processor, mock_model_run_data):
    """
    Unit test for the `initialize_station_prediction` method of the processor.

    This test verifies that the `initialize_station_prediction` method correctly initializes
    a station prediction object using mocked dependencies and ensures that the expected
    calculations and assignments are performed.
    """
    processor, _ = setup_processor
    _, model_run, prediction, station_prediction = mock_model_run_data

    # Mock methods
    processor._weather_station_prediction_initializer = MagicMock(return_value=station_prediction)
    processor._calculate_past_24_hour_precip = MagicMock(return_value=15.0)
    processor._calculate_delta_precip = MagicMock(return_value=5.0)

    # Mock prediction methods
    prediction.get_temp.return_value = 25.0
    prediction.get_rh.return_value = 60.0
    prediction.get_precip.return_value = 10.0
    prediction.get_wind_speed.return_value = 5.5
    prediction.get_wind_direction.return_value = 180.0

    # Call the method
    result = processor.initialize_station_prediction(None, prediction, model_run)

    # Assertions
    processor._weather_station_prediction_initializer.assert_called_once_with(prediction)
    processor._calculate_past_24_hour_precip.assert_called_once_with(
        prediction, station_prediction, model_run
    )
    processor._calculate_delta_precip.assert_called_once_with(None, station_prediction)

    assert math.isclose(result.tmp_tgl_2, 25.0)
    assert math.isclose(result.rh_tgl_2, 60.0)
    assert math.isclose(result.apcp_sfc_0, 10.0)
    assert math.isclose(result.precip_24h, 15.0)
    assert math.isclose(result.delta_precip, 5.0)
    assert math.isclose(result.wind_tgl_10, 5.5)
    assert math.isclose(result.wdir_tgl_10, 180.0)


def test_apply_bias_adjustments(setup_processor, mock_model_run_data):
    """
    Test the `_apply_bias_adjustments` method of the processor.

    This test verifies that the `_apply_bias_adjustments` method correctly applies
    bias adjustments to the station prediction data using a mock machine. It ensures
    that the machine's prediction methods are called with the expected arguments and
    that the returned bias-adjusted values are correctly assigned to the result.
    """
    processor, _ = setup_processor
    _, _, _, station_prediction = mock_model_run_data

    # Mock machine
    machine = MagicMock()

    # Mock machine predictions
    machine.predict_temperature.return_value = 22.5
    machine.predict_rh.return_value = 55.0
    machine.predict_wind_speed.return_value = 6.5
    machine.predict_wind_direction.return_value = 190.0
    machine.predict_precipitation.return_value = 12.0

    # Call the method
    result = processor._apply_bias_adjustments(station_prediction, machine)

    # Assertions
    machine.predict_temperature.assert_called_once_with(
        station_prediction.tmp_tgl_2, station_prediction.prediction_timestamp
    )
    machine.predict_rh.assert_called_once_with(
        station_prediction.rh_tgl_2, station_prediction.prediction_timestamp
    )
    machine.predict_wind_speed.assert_called_once_with(
        station_prediction.wind_tgl_10, station_prediction.prediction_timestamp
    )
    machine.predict_wind_direction.assert_called_once_with(
        station_prediction.wind_tgl_10,
        station_prediction.wdir_tgl_10,
        station_prediction.prediction_timestamp,
    )
    machine.predict_precipitation.assert_called_once_with(
        station_prediction.precip_24h, station_prediction.prediction_timestamp
    )

    assert math.isclose(result.bias_adjusted_temperature, 22.5)
    assert math.isclose(result.bias_adjusted_rh, 55.0)
    assert math.isclose(result.bias_adjusted_wind_speed, 6.5)
    assert math.isclose(result.bias_adjusted_wdir, 190.0)
    assert math.isclose(result.bias_adjusted_precip_24h, 12.0)


def test_apply_interpolated_bias_adjustments(setup_processor, mock_model_run_data):
    """
    Test the `_apply_interpolated_bias_adjustments` method of the processor.

    This test verifies that the method correctly applies interpolated bias adjustments
    to weather model predictions using a machine learning model and interpolation logic.
    """
    processor, _ = setup_processor
    _, _, prediction, station_prediction = mock_model_run_data

    # Mock previous prediction
    prev_prediction = MagicMock(spec=ModelRunPrediction)
    prev_prediction.prediction_timestamp = datetime(2023, 10, 1, 18, 0)

    # Mock current prediction
    prediction.prediction_timestamp = datetime(2023, 10, 1, 21, 0)

    # Mock machine
    machine = MagicMock()
    machine.predict_temperature.side_effect = [10.0, 20.0]
    machine.predict_rh.side_effect = [50.0, 55.0]
    machine.predict_wind_speed.side_effect = [5.0, 6.0]
    machine.predict_wind_direction.side_effect = [180.0, 190.0]
    machine.predict_precipitation.return_value = 10.0

    # Mock interpolation method
    processor.interpolate_20_00_values = MagicMock(side_effect=[16.66, 52.5, 5.5, 185.0])

    # Call the method
    result = processor._apply_interpolated_bias_adjustments(
        station_prediction, prev_prediction, prediction, machine
    )

    # Assertions
    machine.predict_temperature.assert_any_call(
        station_prediction.tmp_tgl_2, prev_prediction.prediction_timestamp
    )
    machine.predict_temperature.assert_any_call(
        station_prediction.tmp_tgl_2, prediction.prediction_timestamp
    )

    machine.predict_rh.assert_any_call(
        station_prediction.rh_tgl_2, prev_prediction.prediction_timestamp
    )
    machine.predict_rh.assert_any_call(station_prediction.rh_tgl_2, prediction.prediction_timestamp)

    machine.predict_wind_speed.assert_any_call(
        station_prediction.wind_tgl_10, prev_prediction.prediction_timestamp
    )
    machine.predict_wind_speed.assert_any_call(
        station_prediction.wind_tgl_10, prediction.prediction_timestamp
    )

    machine.predict_wind_direction.assert_any_call(
        station_prediction.wind_tgl_10,
        station_prediction.wdir_tgl_10,
        prev_prediction.prediction_timestamp,
    )
    machine.predict_wind_direction.assert_any_call(
        station_prediction.wind_tgl_10,
        station_prediction.wdir_tgl_10,
        prediction.prediction_timestamp,
    )

    machine.predict_precipitation.assert_called_once_with(
        station_prediction.precip_24h, station_prediction.prediction_timestamp
    )

    assert processor.interpolate_20_00_values.call_args_list == [
        call(
            prev_prediction.prediction_timestamp,
            prediction.prediction_timestamp,
            10.0,
            20.0,
            datetime(2023, 10, 1, 20, 0),
        ),
        call(
            prev_prediction.prediction_timestamp,
            prediction.prediction_timestamp,
            50.0,
            55.0,
            datetime(2023, 10, 1, 20, 0),
        ),
        call(
            prev_prediction.prediction_timestamp,
            prediction.prediction_timestamp,
            5.0,
            6.0,
            datetime(2023, 10, 1, 20, 0),
        ),
        call(
            prev_prediction.prediction_timestamp,
            prediction.prediction_timestamp,
            180.0,
            190.0,
            datetime(2023, 10, 1, 20, 0),
        ),
    ]

    # precip is not interpolated
    assert processor.interpolate_20_00_values.call_count == 4

    assert result.bias_adjusted_temperature == pytest.approx(16.66, rel=0.1)
    assert result.bias_adjusted_rh == pytest.approx(52.5, rel=0.1)
    assert result.bias_adjusted_wind_speed == pytest.approx(5.5, rel=0.1)
    assert result.bias_adjusted_wdir == pytest.approx(185.0, rel=0.1)
    assert result.bias_adjusted_precip_24h == pytest.approx(10.0, rel=0.1)
