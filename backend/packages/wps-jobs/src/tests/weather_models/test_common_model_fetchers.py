from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
import weather_model_jobs.common_model_fetchers as common_model_fetchers
from weather_model_jobs.common_model_fetchers import (
    ModelValueProcessor,
    RunStager,
    accumulate_nam_precipitation,
    model_run_timestamp,
    run_is_published,
)
from weather_model_jobs.model_values import ModelValues, StationPrediction
from wps_shared.schemas.stations import WeatherStation
from wps_shared.weather_models import ModelEnum
from wps_weather_data.by_time import DAILY, HOURLY, ByTimeTable
from wps_weather_data.runs import RunsTable
from wps_weather_data.staging import StagedFile, StagingTable

ZERO_HOUR_TIMESTAMP = datetime(2023, 9, 7, 0, 0, 0)
TWELVE_HOUR_TIMESTAMP = datetime(2023, 9, 7, 12, 0, 0)
NON_ACCUMULATING_HOUR_TIMESTAMP = datetime(2023, 9, 7, 20, 0, 0)
MODEL_RUN_ZERO_HOUR = 0
MODEL_RUN_SIX_HOUR = 6
MODEL_RUN_TWELVE_HOUR = 12
MODEL_RUN_EIGHTEEN_HOUR = 18


def test_accumulator_is_zero_prediction_apcp_sfc_0_is_none():
    nam_cumulative_precip = 0.0
    prediction = ModelValues(apcp_sfc_0=None, prediction_timestamp=ZERO_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_ZERO_HOUR
    )
    assert cumulative_precip == 0.0
    assert prediction_precip == 0.0


def test_accumulator_has_value_prediction_apcp_sfc_0_is_none():
    nam_cumulative_precip = 1.0
    prediction = ModelValues(apcp_sfc_0=None, prediction_timestamp=ZERO_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_ZERO_HOUR
    )
    assert cumulative_precip == 1.0
    assert prediction_precip == 1.0


def test_accumulator_has_value_prediction_apcp_sfc_0_is_zero():
    nam_cumulative_precip = 1.0
    prediction = ModelValues(apcp_sfc_0=0.0, prediction_timestamp=ZERO_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_ZERO_HOUR
    )
    assert cumulative_precip == 1.0
    assert prediction_precip == 1.0


def test_accumulator_has_value_prediction_apcp_sfc_0_has_value():
    nam_cumulative_precip = 1.0
    prediction = ModelValues(apcp_sfc_0=1.0, prediction_timestamp=ZERO_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_ZERO_HOUR
    )
    assert cumulative_precip == 2.0
    assert prediction_precip == 2.0


def test_zero_hour_timstamp_with_accumulating_hour_timestamp():
    nam_cumulative_precip = 1.0
    prediction = ModelValues(apcp_sfc_0=1.0, prediction_timestamp=NON_ACCUMULATING_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_ZERO_HOUR
    )
    assert cumulative_precip == 1.0
    assert prediction_precip == 2.0


def test_zero_hour_model_run_with_accumulating_timestamp():
    nam_cumulative_precip = 1.0
    prediction = ModelValues(apcp_sfc_0=1.0, prediction_timestamp=TWELVE_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_ZERO_HOUR
    )
    assert cumulative_precip == 2.0
    assert prediction_precip == 2.0


def test_zero_hour_model_run_with_non_accumulating_timestamp():
    nam_cumulative_precip = 1.0
    prediction = ModelValues(apcp_sfc_0=1.0, prediction_timestamp=NON_ACCUMULATING_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_ZERO_HOUR
    )
    assert cumulative_precip == 1.0
    assert prediction_precip == 2.0


def test_six_hour_model_run_with_accumulating_timestamp():
    nam_cumulative_precip = 1.0
    prediction = ModelValues(apcp_sfc_0=1.0, prediction_timestamp=TWELVE_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_SIX_HOUR
    )
    assert cumulative_precip == 2.0
    assert prediction_precip == 2.0


def test_six_hour_model_run_with_non_accumulating_timestamp():
    nam_cumulative_precip = 1.0
    prediction = ModelValues(apcp_sfc_0=1.0, prediction_timestamp=NON_ACCUMULATING_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_SIX_HOUR
    )
    assert cumulative_precip == 1.0
    assert prediction_precip == 2.0


def test_twelve_hour_model_run_with_accumulating_timestamp():
    nam_cumulative_precip = 1.0
    prediction = ModelValues(apcp_sfc_0=1.0, prediction_timestamp=TWELVE_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_TWELVE_HOUR
    )
    assert cumulative_precip == 2.0
    assert prediction_precip == 2.0


def test_twelve_hour_model_run_with_non_accumulating_timestamp():
    nam_cumulative_precip = 1.0
    prediction = ModelValues(apcp_sfc_0=1.0, prediction_timestamp=NON_ACCUMULATING_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_TWELVE_HOUR
    )
    assert cumulative_precip == 1.0
    assert prediction_precip == 2.0


def test_eighteen_hour_model_run_with_accumulating_timestamp():
    nam_cumulative_precip = 1.0
    prediction = ModelValues(apcp_sfc_0=1.0, prediction_timestamp=TWELVE_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_EIGHTEEN_HOUR
    )
    assert cumulative_precip == 2.0
    assert prediction_precip == 2.0


def test_eighteen_hour_model_run_with_non_accumulating_timestamp():
    nam_cumulative_precip = 1.0
    prediction = ModelValues(apcp_sfc_0=1.0, prediction_timestamp=NON_ACCUMULATING_HOUR_TIMESTAMP)
    cumulative_precip, prediction_precip = accumulate_nam_precipitation(
        nam_cumulative_precip, prediction, MODEL_RUN_EIGHTEEN_HOUR
    )
    assert cumulative_precip == 1.0
    assert prediction_precip == 2.0


@pytest.fixture
def mock_station():
    return WeatherStation(code=1215, name="STATION", lat=50.0, long=-120.0)


RUN_TS = datetime(2025, 6, 5, 6, tzinfo=UTC)


@pytest.fixture
def mock_machine():
    return MagicMock()


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def stations(mock_station):
    return [mock_station]


@pytest.fixture
def processor(mock_session, stations):
    # Patch get_stations_synchronously to avoid network calls. The tables are local (conftest).
    with patch(
        "weather_model_jobs.common_model_fetchers.get_stations_synchronously",
        return_value=stations,
    ):
        return ModelValueProcessor(mock_session, ModelEnum.GDPS)


@pytest.fixture
def mock_prediction():
    return ModelValues(
        station_code=1215,
        prediction_timestamp=datetime(2025, 6, 5, 12, tzinfo=UTC),
        tmp_tgl_2=10.0,
        rh_tgl_2=50.0,
        apcp_sfc_0=2.0,
        wind_tgl_10=5.0,
        wdir_tgl_10=180.0,
    )


@pytest.fixture
def mock_station_prediction():
    station_prediction = MagicMock()
    station_prediction.apcp_sfc_0 = 1.0
    return station_prediction


@patch("weather_model_jobs.common_model_fetchers.get_accumulated_precipitation", return_value=3.0)
def test_process_prediction_populates_fields_and_accumulates_correct_precip(
    mock_get_accumulated_precipitation,
    processor,
    mock_prediction,
    mock_station,
    mock_machine,
    mock_session,
):
    processor._add_bias_adjustments_to_prediction = MagicMock()
    processor._add_interpolated_bias_adjustments_to_prediction = MagicMock()
    station_predictions = {}

    processor._process_prediction(
        mock_prediction,
        mock_station,
        RUN_TS,
        mock_machine,
        False,
        station_predictions,
    )

    station_prediction = station_predictions[mock_prediction.prediction_timestamp]
    assert station_prediction.station_code == mock_station.code
    assert station_prediction.prediction_timestamp == mock_prediction.prediction_timestamp
    assert station_prediction.tmp_tgl_2 == pytest.approx(10.0)
    assert station_prediction.rh_tgl_2 == pytest.approx(50.0)
    assert station_prediction.apcp_sfc_0 == pytest.approx(2.0)
    assert station_prediction.wind_tgl_10 == pytest.approx(5.0)
    assert station_prediction.wdir_tgl_10 == pytest.approx(180.0)
    # The first prediction of the run: delta precip is its accumulated precip.
    assert station_prediction.delta_precip == pytest.approx(2.0)
    # No prediction 24 hours earlier in the run, so observed precip makes up the difference.
    assert station_prediction.precip_24h == pytest.approx(5.0)
    assert station_prediction.is_interpolated is False
    processor._add_bias_adjustments_to_prediction.assert_called_once_with(
        station_prediction, mock_machine
    )
    processor._add_interpolated_bias_adjustments_to_prediction.assert_not_called()
    mock_get_accumulated_precipitation.assert_called_once_with(
        mock_session,
        mock_station.code,
        mock_prediction.prediction_timestamp - timedelta(hours=24),
        RUN_TS,
    )


@patch("weather_model_jobs.common_model_fetchers.get_accumulated_precipitation")
def test_process_prediction_uses_the_run_for_24h_and_delta_precip(
    mock_get_accumulated_precipitation, processor, mock_prediction, mock_station, mock_machine
):
    processor._add_bias_adjustments_to_prediction = MagicMock()
    day_before = mock_prediction.prediction_timestamp - timedelta(days=1)
    hour_before = mock_prediction.prediction_timestamp - timedelta(hours=3)
    station_predictions = {
        day_before: StationPrediction(prediction_timestamp=day_before, apcp_sfc_0=0.5),
        hour_before: StationPrediction(prediction_timestamp=hour_before, apcp_sfc_0=1.25),
    }

    processor._process_prediction(
        mock_prediction, mock_station, RUN_TS, mock_machine, False, station_predictions
    )

    station_prediction = station_predictions[mock_prediction.prediction_timestamp]
    assert station_prediction.precip_24h == pytest.approx(1.5)
    assert station_prediction.delta_precip == pytest.approx(0.75)
    mock_get_accumulated_precipitation.assert_not_called()


@patch("weather_model_jobs.common_model_fetchers.get_accumulated_precipitation", return_value=0)
def test_process_prediction_existing_prediction_is_updated(
    _, processor, mock_prediction, mock_station, mock_machine
):
    existing = StationPrediction(prediction_timestamp=mock_prediction.prediction_timestamp)
    station_predictions = {mock_prediction.prediction_timestamp: existing}
    processor._add_bias_adjustments_to_prediction = MagicMock()

    processor._process_prediction(
        mock_prediction, mock_station, RUN_TS, mock_machine, False, station_predictions
    )

    assert station_predictions[mock_prediction.prediction_timestamp] is existing
    assert existing.station_code == mock_station.code
    assert existing.tmp_tgl_2 == pytest.approx(10.0)


@patch("weather_model_jobs.common_model_fetchers.get_accumulated_precipitation", return_value=0)
def test_process_prediction_missing_precip_is_zero(
    _, processor, mock_prediction, mock_station, mock_machine
):
    mock_prediction.apcp_sfc_0 = None
    station_predictions = {}
    processor._add_bias_adjustments_to_prediction = MagicMock()

    processor._process_prediction(
        mock_prediction, mock_station, RUN_TS, mock_machine, False, station_predictions
    )

    assert station_predictions[mock_prediction.prediction_timestamp].apcp_sfc_0 == 0.0


@pytest.mark.parametrize(
    "wind_direction_at_1800,wind_direction_at_2100,expected_direction",
    [
        # 350 and 10 are 20 degrees apart across north. Two-thirds of the way:
        # 350 + 20 * 2/3 = 1090/3; wrap 360 degrees to get 10/3.
        (350.0, 10.0, 10 / 3),
        # Unwrap 10 as 370, then interpolate two-thirds toward 350:
        # 370 + (350 - 370) * 2/3 = 1070/3 degrees.
        (10.0, 350.0, 1070 / 3),
        # If one bias-adjusted direction is unavailable, there is no value to interpolate.
        (None, 350.0, None),
    ],
)
@patch("weather_model_jobs.common_model_fetchers.interpolate_between_two_points", new=MagicMock())
def test_interpolated_bias_adjusted_wind_direction(
    processor,
    mock_machine,
    mock_station_prediction,
    wind_direction_at_1800,
    wind_direction_at_2100,
    expected_direction,
):
    mock_station_prediction.prediction_timestamp = NON_ACCUMULATING_HOUR_TIMESTAMP
    # The method is called at 1800 and then 2100; side_effect supplies the matching directions in order.
    mock_machine.predict_wind_direction.side_effect = [
        wind_direction_at_1800,
        wind_direction_at_2100,
    ]

    processor._add_interpolated_bias_adjustments_to_prediction(
        mock_station_prediction, mock_machine
    )

    if expected_direction is None:
        assert mock_station_prediction.bias_adjusted_wdir is None
    else:
        assert mock_station_prediction.bias_adjusted_wdir == pytest.approx(expected_direction)


def test_model_run_timestamp_is_today_once_the_hour_has_passed():
    now = datetime(2025, 6, 5, 14, 37, tzinfo=UTC)
    assert model_run_timestamp(now, 12) == datetime(2025, 6, 5, 12, tzinfo=UTC)


def test_model_run_timestamp_is_yesterday_before_the_hour():
    now = datetime(2025, 6, 5, 3, 10, tzinfo=UTC)
    assert model_run_timestamp(now, 12) == datetime(2025, 6, 4, 12, tzinfo=UTC)


def stage(staging: StagingTable, run_ts: datetime, source: str, values=()):
    staging.append_files(run_ts, [StagedFile(source, run_ts, list(values))])


def test_run_is_not_published_until_it_is_in_runs():
    runs, staging = RunsTable(), StagingTable(ModelEnum.GDPS)
    assert not run_is_published(runs, staging, ModelEnum.GDPS, RUN_TS)


def test_run_in_runs_with_no_staging_is_published():
    runs, staging = RunsTable(), StagingTable(ModelEnum.GDPS)
    runs.append_run(
        ModelEnum.GDPS, RUN_TS, [{"station_code": 1215, "prediction_timestamp": RUN_TS}]
    )
    assert run_is_published(runs, staging, ModelEnum.GDPS, RUN_TS)


def test_run_in_runs_and_staging_was_interrupted_and_is_not_published():
    runs, staging = RunsTable(), StagingTable(ModelEnum.GDPS)
    runs.append_run(
        ModelEnum.GDPS, RUN_TS, [{"station_code": 1215, "prediction_timestamp": RUN_TS}]
    )
    stage(staging, RUN_TS, "url-1")
    assert not run_is_published(runs, staging, ModelEnum.GDPS, RUN_TS)


def test_run_stager_knows_files_staged_by_an_earlier_invocation():
    staging = StagingTable(ModelEnum.GDPS)
    stage(staging, RUN_TS, "url-1")

    stager = RunStager(staging, RUN_TS)

    assert stager.is_processed("url-1")
    assert not stager.is_processed("url-2")


def test_run_stager_counts_pending_files_as_processed_before_flushing():
    staging = StagingTable(ModelEnum.GDPS)
    stager = RunStager(staging, RUN_TS)

    stager.add("url-1", RUN_TS, [])

    assert stager.is_processed("url-1")
    # Nothing is staged until a flush.
    assert staging.processed_sources(RUN_TS) == set()
    stager.flush()
    assert staging.processed_sources(RUN_TS) == {"url-1"}


def test_run_stager_flushes_in_batches(monkeypatch):
    monkeypatch.setattr(common_model_fetchers, "FILES_PER_STAGING_COMMIT", 2)
    staging = MagicMock()
    staging.processed_sources.return_value = set()
    stager = RunStager(staging, RUN_TS)

    stager.add("url-1", RUN_TS, [])
    staging.append_files.assert_not_called()
    stager.add("url-2", RUN_TS, [])
    staging.append_files.assert_called_once()
    stager.add("url-3", RUN_TS, [])
    stager.flush()

    assert staging.append_files.call_count == 2
    staged = [file.source for call in staging.append_files.call_args_list for file in call.args[1]]
    assert staged == ["url-1", "url-2", "url-3"]
    # A flush with nothing pending stages nothing.
    stager.flush()
    assert staging.append_files.call_count == 2


def test_run_stager_is_complete_once_every_file_is_staged():
    staging = StagingTable(ModelEnum.GDPS)
    stager = RunStager(staging, RUN_TS)
    stager.add("url-1", RUN_TS, [])

    # Pending files do not count until they are staged.
    assert not stager.is_complete(["url-1", "url-2"])
    stager.add("url-2", RUN_TS, [])
    stager.flush()
    assert stager.is_complete(["url-1", "url-2"])
    assert not stager.is_complete([])


def staged_values(time, temperature, precip):
    return [
        (1215, time, "tmp_tgl_2", temperature),
        (1215, time, "rh_tgl_2", 50.0),
        (1215, time, "apcp_sfc_0", precip),
        (1215, time, "wind_tgl_10", 10.0),
        (1215, time, "wdir_tgl_10", 90.0),
    ]


@patch("weather_model_jobs.common_model_fetchers.get_accumulated_precipitation", return_value=0)
@patch("weather_model_jobs.common_model_fetchers.read_model_history")
@patch("weather_model_jobs.common_model_fetchers.StationMachineLearning")
def test_publish_run_writes_runs_and_by_time_and_deletes_staging(
    mock_machine_learning, mock_read_model_history, _, processor
):
    machine = mock_machine_learning.return_value
    machine.predict_temperature.return_value = 11.0
    machine.predict_rh.return_value = 51.0
    machine.predict_wind_speed.return_value = 9.0
    machine.predict_wind_direction.return_value = 95.0
    machine.predict_precipitation.return_value = 1.0
    run_ts = datetime(2025, 6, 5, 12, tzinfo=UTC)
    at_1800 = datetime(2025, 6, 5, 18, tzinfo=UTC)
    at_2100 = datetime(2025, 6, 5, 21, tzinfo=UTC)
    processor.staging_table.append_files(
        run_ts,
        [
            StagedFile("url-18", at_1800, staged_values(at_1800, 10.0, 1.0)),
            StagedFile("url-21", at_2100, staged_values(at_2100, 13.0, 4.0)),
        ],
    )

    processor.process([run_ts])

    mock_read_model_history.assert_called_once_with(processor.runs_table, ModelEnum.GDPS, run_ts)
    rows = processor.runs_table.read(ModelEnum.GDPS, run_ts, run_ts).to_pylist()
    assert [(row["prediction_timestamp"].hour, row["is_interpolated"]) for row in rows] == [
        (18, False),
        (20, True),
        (21, False),
    ]
    noon = rows[1]
    # 2 of the 3 hours from 18:00 to 21:00.
    assert noon["tmp_tgl_2"] == pytest.approx(12.0)
    assert noon["apcp_sfc_0"] == pytest.approx(3.0)
    assert noon["delta_precip"] == pytest.approx(2.0)
    assert rows[2]["delta_precip"] == pytest.approx(1.0)
    assert noon["bias_adjusted_temperature"] == pytest.approx(11.0)
    assert noon["bias_adjusted_precip_24h"] == pytest.approx(1.0)

    by_time = ByTimeTable()
    hourly = by_time.read(HOURLY, ["GDPS"], at_1800, at_2100)
    assert hourly.num_rows == 3
    daily = by_time.read(DAILY, ["GDPS"], at_1800, at_2100).to_pylist()
    assert [row["timestamp"].hour for row in daily] == [20]

    assert not processor.staging_table.has_run(run_ts)


@patch("weather_model_jobs.common_model_fetchers.read_model_history")
def test_publish_run_fails_without_deleting_staging_when_runs_write_fails(_, processor):
    run_ts = datetime(2025, 6, 5, 12, tzinfo=UTC)
    at_1800 = datetime(2025, 6, 5, 18, tzinfo=UTC)
    stage(processor.staging_table, run_ts, "url-1", staged_values(at_1800, 10.0, 1.0))
    processor._process_model_run_for_station = MagicMock(
        return_value=[StationPrediction(station_code=1215, prediction_timestamp=at_1800)]
    )
    processor.runs_table = MagicMock()
    processor.runs_table.append_run.side_effect = OSError("object store is down")
    processor.by_time_table = MagicMock()

    with pytest.raises(OSError):
        processor.publish_run(run_ts)

    processor.by_time_table.merge_run.assert_not_called()
    # Still staged, so the next invocation publishes it again.
    assert processor.staging_table.has_run(run_ts)


@patch("weather_model_jobs.common_model_fetchers.get_accumulated_precipitation", return_value=0)
@patch("weather_model_jobs.common_model_fetchers.read_model_history")
@patch("weather_model_jobs.common_model_fetchers.StationMachineLearning")
def test_nam_precip_is_accumulated_in_the_run(_, __, ___, mock_session, stations):
    with patch(
        "weather_model_jobs.common_model_fetchers.get_stations_synchronously",
        return_value=stations,
    ):
        processor = ModelValueProcessor(mock_session, ModelEnum.NAM)
    run_ts = datetime(2025, 6, 5, 0, tzinfo=UTC)
    times = [run_ts + timedelta(hours=hour) for hour in (12, 15, 24)]
    predictions = [
        ModelValues(station_code=1215, prediction_timestamp=time, tmp_tgl_2=1.0, apcp_sfc_0=1.0)
        for time in times
    ]

    station_predictions = processor._process_model_run_for_station(
        run_ts, stations[0], predictions, history=None
    )

    # The 00Z run's precip is per 12 hours, so the running total only moves on hours 12 and 24.
    assert [p.apcp_sfc_0 for p in station_predictions] == [1.0, 2.0, 2.0]


@patch("weather_model_jobs.common_model_fetchers.read_model_history")
def test_publish_run_with_no_station_predictions_keeps_the_run_in_staging(_, processor):
    run_ts = datetime(2025, 6, 5, 12, tzinfo=UTC)
    at_1800 = datetime(2025, 6, 5, 18, tzinfo=UTC)
    # Values for a station the job does not know, so the run yields no predictions.
    processor.staging_table.append_files(
        run_ts, [StagedFile("url-18", at_1800, [(999, at_1800, "tmp_tgl_2", 10.0)])]
    )

    processor.publish_run(run_ts)

    assert not processor.runs_table.has_run(ModelEnum.GDPS, run_ts)
    assert not ByTimeTable().exists()
    # Still staged, so the next run does not download it all again.
    assert processor.staging_table.processed_sources(run_ts) == {"url-18"}
