import math
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, call

import pyarrow.compute as pc
import pytest
import weather_model_jobs.ecmwf_prediction_processor
from pytest_mock import MockerFixture
from weather_model_jobs import ModelEnum
from weather_model_jobs.ecmwf_prediction_processor import ECMWFPredictionProcessor
from weather_model_jobs.model_values import ModelValues, StationPrediction
from wps_shared.schemas.stations import WeatherStation
from wps_weather_data.by_time import DAILY, HOURLY, ByTimeTable
from wps_weather_data.runs import RunsTable
from wps_weather_data.staging import MODEL_FIELDS, StagedFile, StagingTable

RUN_TS = datetime(2023, 10, 1, 0, tzinfo=timezone.utc)


@pytest.fixture
def tables(tmp_path):
    return (
        RunsTable(str(tmp_path / "runs")),
        ByTimeTable(str(tmp_path / "by_time")),
        StagingTable(ModelEnum.ECMWF, str(tmp_path / "staging")),
    )


@pytest.fixture
def setup_processor(tables):
    stations = [
        WeatherStation(code=1, long=10.0, lat=50.0, name="Station 1"),
        WeatherStation(code=1, long=20.0, lat=60.0, name="Station 2"),
    ]
    runs, by_time, staging = tables
    processor = ECMWFPredictionProcessor(
        stations, runs_table=runs, by_time_table=by_time, staging_table=staging
    )
    return processor, processor.observations


@pytest.fixture
def mock_predictions():
    processor = ECMWFPredictionProcessor([])
    prev_prediction = MagicMock(spec=ModelValues)
    prediction = MagicMock(spec=ModelValues)
    return processor, prev_prediction, prediction


@pytest.fixture
def mock_model_run_data():
    station = WeatherStation(code=1, long=10.0, lat=50.0, name="Station 1")
    run_ts = datetime(2023, 10, 2, 11, 0)
    prediction = MagicMock(spec=ModelValues)
    prediction.station_code = station.code
    prediction.prediction_timestamp = datetime(2023, 10, 2, 12, 0)
    station_prediction = MagicMock()
    station_prediction.prediction_timestamp = datetime(2023, 10, 2, 12, 0)
    station_prediction.apcp_sfc_0 = 0.0
    return station, run_ts, prediction, station_prediction


@pytest.fixture
def mock_machine(mocker: MockerFixture):
    """A trained machine whose bias adjustments are fixed values."""
    machine_class = mocker.patch(
        "weather_model_jobs.ecmwf_prediction_processor.StationMachineLearning"
    )
    machine = machine_class.return_value
    machine.predict_temperature.return_value = 11.0
    machine.predict_rh.return_value = 51.0
    machine.predict_wind_speed.return_value = 6.0
    machine.predict_wind_direction.return_value = 181.0
    machine.predict_precipitation.return_value = 1.5
    return machine_class


def test_process_model_run_for_station(setup_processor, mocker: MockerFixture, mock_machine):
    """
    Test the `_process_model_run_for_station` method of the processor.

    This test verifies that the processor correctly handles the processing of
    model run predictions for a given weather station, including applying bias
    adjustments and interpolated bias adjustments.
    """
    processor, _ = setup_processor

    # Mock data
    station = WeatherStation(code=1, long=10.0, lat=50.0, name="Station 1")
    model_run_predictions = [
        ModelValues(
            station_code=1, prediction_timestamp=datetime(2023, 10, 1, 18, 0), apcp_sfc_0=0.0
        ),
        ModelValues(
            station_code=1, prediction_timestamp=datetime(2023, 10, 1, 21, 0), apcp_sfc_0=0.0
        ),
    ]
    interpolated_noon_prediction_spy = mocker.spy(
        weather_model_jobs.ecmwf_prediction_processor,
        "construct_interpolated_noon_prediction",
    )
    initialize_station_prediction_spy = mocker.spy(processor, "initialize_station_prediction")

    # Mock methods
    processor._apply_bias_adjustments = MagicMock(side_effect=lambda prediction, _: prediction)
    processor._apply_interpolated_bias_adjustments = MagicMock(
        side_effect=lambda prediction, *_: prediction
    )
    mocker.patch.object(processor, "_has_expected_timestamp_coverage", return_value=True)

    # Call the method
    result = processor._process_model_run_for_station(
        RUN_TS, station, model_run_predictions, history=None
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
    assert initialize_station_prediction_spy.call_args_list[1][0][1] is not model_run_predictions[0]
    assert initialize_station_prediction_spy.call_args_list[1][0][1] is not model_run_predictions[1]
    # one station prediction per time, in time order, the noon one marked as interpolated
    assert [(p.prediction_timestamp.hour, p.is_interpolated) for p in result] == [
        (18, False),
        (20, True),
        (21, False),
    ]
    mock_machine.assert_called_once()
    assert mock_machine.call_args.kwargs["max_learn_date"] == RUN_TS


def test_process_model_run_for_station_skips_incomplete_coverage(
    setup_processor, mocker: MockerFixture, caplog
):
    processor, _ = setup_processor
    station = WeatherStation(code=6216, long=-121.0, lat=51.0, name="QD 15 CHASM")
    run_ts = datetime(2026, 8, 8, tzinfo=timezone.utc)
    model_run_predictions = [
        ModelValues(station_code=6216, prediction_timestamp=run_ts + timedelta(hours=hour))
        for hour in [69, 75, 81, 84, 144, 162]
    ]
    station_machine_learning = mocker.patch(
        "weather_model_jobs.ecmwf_prediction_processor.StationMachineLearning"
    )

    result = processor._process_model_run_for_station(
        run_ts, station, model_run_predictions, history=None
    )

    station_machine_learning.assert_not_called()
    assert result == []
    assert "expected=65, actual=6, missing=59, unexpected=0" in caplog.text


def test_expected_timestamp_coverage_accepts_complete_run(setup_processor):
    processor, _ = setup_processor
    station = WeatherStation(code=1, long=10.0, lat=50.0, name="Station 1")
    run_ts = datetime(2026, 8, 8, tzinfo=timezone.utc)
    predictions = [
        ModelValues(station_code=1, prediction_timestamp=run_ts + timedelta(hours=hour))
        for hour in weather_model_jobs.ecmwf_prediction_processor.get_ecmwf_forecast_hours()
    ]

    assert processor._has_expected_timestamp_coverage(run_ts, station, predictions)


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
    """
    processor, prev_prediction, prediction = mock_predictions

    # Mock timestamps where next timestamp is earlier than previous timestamp
    prev_prediction.prediction_timestamp = prev_timestamp
    prediction.prediction_timestamp = next_timestamp

    with pytest.raises(AssertionError, match=expected):
        processor._should_interpolate(prev_prediction, prediction)


def test_initialize_station_prediction_creates_new_prediction(setup_processor):
    processor, _ = setup_processor
    prediction = ModelValues(
        station_code=123,
        prediction_timestamp=datetime(2023, 10, 1, 12, 0),
        tmp_tgl_2=1.0,
        rh_tgl_2=2.0,
        apcp_sfc_0=3.0,
        wdir_tgl_10=4.0,
        wind_tgl_10=5.0,
    )
    processor._calculate_past_24_hour_precip = MagicMock(return_value=7.0)
    station_predictions = {}

    station_prediction = processor.initialize_station_prediction(
        None, prediction, RUN_TS, station_predictions
    )

    assert isinstance(station_prediction, StationPrediction)
    assert station_prediction.station_code == 123
    assert station_prediction.prediction_timestamp == prediction.prediction_timestamp
    assert (station_prediction.tmp_tgl_2, station_prediction.rh_tgl_2) == (1.0, 2.0)
    assert station_prediction.apcp_sfc_0 == 3.0
    assert (station_prediction.wdir_tgl_10, station_prediction.wind_tgl_10) == (4.0, 5.0)
    assert station_prediction.precip_24h == 7.0
    # the first prediction of a run has no previous one, so all its precip is new
    assert station_prediction.delta_precip == 3.0


def test_initialize_station_prediction_updates_existing_prediction(setup_processor):
    processor, _ = setup_processor
    timestamp = datetime(2023, 10, 1, 12, 0)
    existing = StationPrediction(
        station_code=123, prediction_timestamp=timestamp, bias_adjusted_temperature=9.0
    )
    prediction = ModelValues(station_code=123, prediction_timestamp=timestamp, tmp_tgl_2=1.0)
    processor._calculate_past_24_hour_precip = MagicMock(return_value=0.0)

    station_prediction = processor.initialize_station_prediction(
        None, prediction, RUN_TS, {timestamp: existing}
    )

    assert station_prediction is existing
    assert station_prediction.tmp_tgl_2 == 1.0
    assert station_prediction.bias_adjusted_temperature == 9.0


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
    setup_processor, mock_model_run_data, mocker: MockerFixture
):
    """
    The past 24 hour precip is the difference with the run's own prediction 24 hours earlier.
    """
    processor, _ = setup_processor
    _, run_ts, prediction, station_prediction = mock_model_run_data
    actual_precip = mocker.patch(
        "weather_model_jobs.ecmwf_prediction_processor.get_accumulated_precipitation"
    )
    previous_prediction = StationPrediction(apcp_sfc_0=5.0)
    station_predictions = {prediction.prediction_timestamp - timedelta(days=1): previous_prediction}

    result = processor._calculate_past_24_hour_precip(
        prediction, station_prediction, run_ts, station_predictions
    )

    actual_precip.assert_not_called()
    assert math.isclose(result, 5.0)


def test_calculate_past_24_hour_precip_without_previous_prediction(
    setup_processor, mock_model_run_data, mocker: MockerFixture
):
    """
    Without a prediction 24 hours earlier in the run, observed precip makes up the hours
    before the run started.
    """
    processor, observations = setup_processor
    _, run_ts, prediction, station_prediction = mock_model_run_data
    actual_precip = mocker.patch(
        "weather_model_jobs.ecmwf_prediction_processor.get_accumulated_precipitation",
        return_value=3.0,
    )

    result = processor._calculate_past_24_hour_precip(prediction, station_prediction, run_ts, {})

    actual_precip.assert_called_once_with(
        observations,
        prediction.station_code,
        prediction.prediction_timestamp - timedelta(days=1),
        run_ts,
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


def test_process_publishes_each_run(setup_processor):
    processor, _ = setup_processor
    processor.publish_run = MagicMock()
    later_run = RUN_TS + timedelta(hours=12)

    processor.process([RUN_TS, later_run])

    assert processor.publish_run.call_args_list == [call(RUN_TS), call(later_run)]


def stage_run(staging: StagingTable, run_ts: datetime, station_code: int, hours: list[int]):
    """Stage one file per forecast hour, each with every model field for the station."""
    files = []
    for hour in hours:
        timestamp = run_ts + timedelta(hours=hour)
        values = {
            "tmp_tgl_2": 10.0 + hour,
            "rh_tgl_2": 50.0,
            "apcp_sfc_0": float(hour),
            "wdir_tgl_10": 180.0,
            "wind_tgl_10": 5.0,
        }
        files.append(
            StagedFile(
                f"fxx={hour:03d}",
                timestamp,
                [(station_code, timestamp, field, values[field]) for field in MODEL_FIELDS],
            )
        )
    staging.append_files(run_ts, files)


def test_publish_run_processes_each_station(setup_processor, tables):
    processor, _ = setup_processor
    _, _, staging = tables
    stations = [
        WeatherStation(code=1, long=10.0, lat=50.0, name="Station 1"),
        WeatherStation(code=2, long=20.0, lat=60.0, name="Station 2"),
    ]
    processor.stations = stations
    stage_run(staging, RUN_TS, 1, [18, 21])
    processor._process_model_run_for_station = MagicMock(return_value=[])

    processor.publish_run(RUN_TS)

    assert processor._process_model_run_for_station.call_count == len(stations)
    first, second = processor._process_model_run_for_station.call_args_list
    assert first.args[0] == RUN_TS
    assert first.args[1] == stations[0]
    assert [prediction.prediction_timestamp.hour for prediction in first.args[2]] == [18, 21]
    # a station with nothing staged gets no predictions
    assert second.args[1] == stations[1]
    assert second.args[2] == []


def test_publish_run_writes_runs_and_by_time_and_deletes_staging(
    setup_processor, tables, mocker: MockerFixture, mock_machine
):
    processor, _ = setup_processor
    runs, by_time, staging = tables
    processor.stations = [WeatherStation(code=1, long=10.0, lat=50.0, name="Station 1")]
    stage_run(staging, RUN_TS, 1, [18, 21])
    mocker.patch.object(processor, "_has_expected_timestamp_coverage", return_value=True)
    mocker.patch(
        "weather_model_jobs.ecmwf_prediction_processor.get_accumulated_precipitation",
        return_value=0.0,
    )

    processor.process([RUN_TS])

    rows = runs.read(ModelEnum.ECMWF, RUN_TS, RUN_TS).to_pylist()
    assert [(row["prediction_timestamp"].hour, row["is_interpolated"]) for row in rows] == [
        (18, False),
        (20, True),
        (21, False),
    ]
    noon = rows[1]
    assert noon["station_code"] == 1
    assert noon["tmp_tgl_2"] == pytest.approx(10.0 + 18 + (21 - 18) * 2 / 3)
    assert noon["bias_adjusted_precip_24h"] == pytest.approx(1.5)

    end = RUN_TS + timedelta(days=1)
    hourly = by_time.read(HOURLY, [ModelEnum.ECMWF.value], RUN_TS, end)
    assert pc.hour(hourly["timestamp"]).to_pylist() == [18, 20, 21]
    daily = by_time.read(DAILY, [ModelEnum.ECMWF.value], RUN_TS, end)
    assert pc.hour(daily["timestamp"]).to_pylist() == [20]

    assert not staging.has_run(RUN_TS)


def test_apply_bias_adjustments(setup_processor, mock_model_run_data):
    """
    Test the `_apply_bias_adjustments` method of the processor.
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
    """
    processor, _ = setup_processor
    _, _, prediction, station_prediction = mock_model_run_data

    # Mock previous prediction
    prev_prediction = MagicMock(spec=ModelValues)
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


def test_publish_run_with_no_station_predictions_keeps_the_run_in_staging(
    setup_processor, tables, mocker: MockerFixture
):
    processor, _ = setup_processor
    runs, by_time, staging = tables
    mocker.patch.object(weather_model_jobs.ecmwf_prediction_processor, "read_model_history")
    # One forecast hour only, so no station has the coverage to be processed.
    stage_run(staging, RUN_TS, 1, [0])

    processor.publish_run(RUN_TS)

    assert not runs.has_run(ModelEnum.ECMWF, RUN_TS)
    assert not by_time.exists()
    assert staging.processed_sources(RUN_TS) == {"fxx=000"}


def test_a_publish_interrupted_is_finished_without_appending_again(
    setup_processor, tables, mocker: MockerFixture
):
    processor, _ = setup_processor
    runs, by_time, staging = tables
    processor.stations = [WeatherStation(code=1, long=10.0, lat=50.0, name="Station 1")]
    stage_run(staging, RUN_TS, 1, [18])
    at_1800 = RUN_TS + timedelta(hours=18)
    process_station = mocker.patch.object(
        processor,
        "_process_model_run_for_station",
        return_value=[StationPrediction(station_code=1, prediction_timestamp=at_1800)],
    )
    merge = mocker.patch.object(by_time, "_merge", side_effect=MemoryError)
    with pytest.raises(MemoryError):
        processor.publish_run(RUN_TS)
    mocker.stop(merge)

    processor.publish_run(RUN_TS)

    assert process_station.call_count == 1
    versions = runs.dataset().to_table(columns=["ingested_at"])["ingested_at"].to_pylist()
    assert len(versions) == 1
    assert by_time.read(HOURLY, [ModelEnum.ECMWF.value], at_1800, at_1800).num_rows == 1
    assert not staging.has_run(RUN_TS)
