import math
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, PropertyMock

import numpy as np
import pytest
import weather_model_jobs.ecmwf
import xarray as xr
from aiohttp import ClientSession
from pytest_mock import MockerFixture
from weather_model_jobs import ModelEnum
from weather_model_jobs.ecmwf import (
    ECMWF,
    forecast_hour_source,
    get_ecmwf_forecast_hours,
    get_model_run_hours,
    get_stations_dataframe,
    station_values,
)
from weather_model_jobs.ecmwf_model_processor import ECMWFModelProcessor
from wps_shared.geospatial.bounds import (
    BC_MAX_LATITUDE,
    BC_MAX_LONGITUDE,
    BC_MIN_LATITUDE,
    BC_MIN_LONGITUDE,
)
from wps_shared.schemas.stations import WeatherStation
from wps_shared.tests.common import default_mock_client_get
from wps_weather_data.runs import RunsTable
from wps_weather_data.staging import StagedFile, StagingTable

num_forecast_hours = len(list(get_ecmwf_forecast_hours()))

NOW = datetime(2026, 11, 13, 18, tzinfo=timezone.utc)
RUN_TS = datetime(2026, 11, 13, tzinfo=timezone.utc)


def raise_system_exit(code: int):
    raise SystemExit(code)


@pytest.fixture
def mock_stations():
    return [
        WeatherStation(code="001", name="Station1", lat=10.0, long=20.0),
        WeatherStation(code="002", name="Station2", lat=15.0, long=25.0),
    ]


@pytest.fixture
def staging(tmp_path):
    return StagingTable(ModelEnum.ECMWF, str(tmp_path / "staging"))


@pytest.fixture
def runs(tmp_path):
    return RunsTable(str(tmp_path / "runs"))


def make_ecmwf(staging, runs, stations=None, now=NOW) -> ECMWF:
    ecmwf = ECMWF("/tmp", stations or [], staging_table=staging, runs_table=runs)
    ecmwf.now = now
    return ecmwf


def publish(runs: RunsTable, run_ts: datetime):
    """Put a run in `runs`, as a published run would be."""
    runs.append_run(ModelEnum.ECMWF, run_ts, [{"station_code": 1, "prediction_timestamp": run_ts}])


def stage_hours(staging: StagingTable, run_ts: datetime, hours):
    staging.append_files(
        run_ts,
        [StagedFile(forecast_hour_source(hour), run_ts + timedelta(hours=hour)) for hour in hours],
    )


@pytest.fixture
def mock_herbie_instance(mocker: MockerFixture):
    """Fixture to set up a mocked Herbie instance."""
    mock_herbie = MagicMock()
    mocker.patch("weather_model_jobs.ecmwf.Herbie", mock_herbie)
    mock_herbie_instance = MagicMock()
    mock_herbie.return_value = mock_herbie_instance
    mock_herbie_instance.download.return_value = "/path/to/mock/file.grib"
    mock_herbie_instance.grib = "/path/to/mock/file.grib"
    mock_herbie_instance.SOURCES = {"mock": mock_herbie_instance.grib}
    yield mock_herbie_instance


@pytest.fixture
def mock_forecast_processing(mocker: MockerFixture):
    """Process every forecast without touching GRIB files, staging no station values."""
    mocker.patch("weather_model_jobs.ecmwf.get_ecmwf_transformer", return_value=MagicMock())
    mocker.patch("weather_model_jobs.ecmwf.get_stations_dataframe", return_value=MagicMock())
    mocker.patch.object(ECMWFModelProcessor, "process_grib_data", return_value=MagicMock())
    mocker.patch("weather_model_jobs.ecmwf.station_values", return_value=[])


def make_herbie_forecast(hour, mirror, resolution="0p1", signature="token"):
    path = f"20261112/00z/ifs/{resolution}/oper/20261112000000-{hour}h-oper-fc-sfc.grib2"
    sources = {
        "google": f"https://storage.googleapis.com/ecmwf-open-data/{path}",
        "aws": f"https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/{path}",
        "azure": f"https://ai4edataeuwest.blob.core.windows.net/ecmwf/{path}",
    }
    url = sources[mirror]
    if mirror == "azure":
        url += f"?sig={signature}"
    return MagicMock(grib=url, SOURCES=sources)


@pytest.mark.parametrize(
    "first_mirror, next_mirror",
    [("google", "aws"), ("azure", "aws"), ("google", "azure"), ("azure", "azure")],
)
def test_process_model_run_resumes_after_mirror_change(
    mocker, staging, runs, first_mirror, next_mirror
):
    """A forecast hour staged from one mirror is not fetched again from another."""
    first_forecast = make_herbie_forecast(0, first_mirror, signature="first")
    pending_forecast = make_herbie_forecast(3, next_mirror, signature="second")
    herbie = mocker.patch(
        "weather_model_jobs.ecmwf.Herbie",
        side_effect=[first_forecast, MagicMock(grib=None), pending_forecast],
    )
    mocker.patch("weather_model_jobs.ecmwf.get_ecmwf_forecast_hours", return_value=[0, 3])
    ecmwf = make_ecmwf(staging, runs, now=datetime(2026, 11, 12, 10, tzinfo=timezone.utc))
    process_forecast = mocker.patch.object(ecmwf, "_process_forecast_with_retry", return_value=[])
    run_ts = datetime(2026, 11, 12, tzinfo=timezone.utc)

    ecmwf.process_model_run(0)

    assert staging.processed_sources(run_ts) == {forecast_hour_source(0)}
    assert ecmwf.files_processed == 1
    assert ecmwf.complete_runs == []

    ecmwf.process_model_run(0)

    # hour 0 is already staged, so only hour 3 is looked up on the second run
    assert [call.kwargs["fxx"] for call in herbie.call_args_list] == [0, 3, 3]
    assert [call.kwargs["url"] for call in process_forecast.call_args_list] == [
        first_forecast.grib,
        pending_forecast.grib,
    ]
    assert staging.processed_sources(run_ts) == {forecast_hour_source(0), forecast_hour_source(3)}
    assert ecmwf.files_processed == 2
    assert ecmwf.exception_count == 0
    assert ecmwf.complete_runs == [run_ts]


def test_get_model_run_hours():
    hours = list(get_model_run_hours(ModelEnum.ECMWF))
    assert hours == [0, 12]


def test_get_ecmwf_forecast_hours():
    hours = list(get_ecmwf_forecast_hours())
    assert hours[:5] == [0, 3, 6, 9, 12]
    assert hours[-5:] == [216, 222, 228, 234, 240]


def test_forecast_hour_source():
    assert forecast_hour_source(3) == "fxx=003"
    assert forecast_hour_source(240) == "fxx=240"


def test_get_stations_dataframe():
    transformer = MagicMock()
    transformer.transform.side_effect = lambda x, y: (x + 1, y + 1)
    stations = [
        WeatherStation(code="001", name="Station1", lat=10.0, long=20.0),
        WeatherStation(code="002", name="Station2", lat=15.0, long=25.0),
    ]
    df = get_stations_dataframe(transformer, stations)
    assert len(df) == 2
    assert math.isclose(df.iloc[0]["latitude"], 11.0)
    assert math.isclose(df.iloc[0]["longitude"], 21.0)


def test_ecmwf_process_model_run_no_url(mock_herbie_instance, staging, runs):
    mock_herbie_instance.grib = None
    stations = [WeatherStation(code="001", name="Station1", lat=10.0, long=20.0)]
    ecmwf = make_ecmwf(staging, runs, stations)
    ecmwf.process_model_run(0)

    assert ecmwf.files_downloaded == 0
    assert ecmwf.files_processed == 0
    assert ecmwf.complete_runs == []
    assert not staging.has_run(RUN_TS)


def test_process_model_run_requests_0p1_surface_model(mock_herbie_instance, staging, runs):
    mock_herbie_instance.grib = None
    ecmwf = make_ecmwf(staging, runs)

    ecmwf.process_model_run(0)

    herbie_kwargs = weather_model_jobs.ecmwf.Herbie.call_args.kwargs
    assert herbie_kwargs["model"] == "ifs"
    assert herbie_kwargs["product"] == "oper"
    assert herbie_kwargs["resolution"] == "0p1"
    assert herbie_kwargs["levtype"] == "sfc"
    assert "priority" not in herbie_kwargs
    assert ecmwf.complete_runs == []


@pytest.mark.parametrize(
    "published, expected_processed, expected_complete",
    [(False, num_forecast_hours, [RUN_TS]), (True, 0, [])],
)
def test_ecmwf_process_model_complete(
    published,
    expected_processed,
    expected_complete,
    mock_herbie_instance,
    mock_forecast_processing,
    staging,
    runs,
):
    if published:
        publish(runs, RUN_TS)
    stations = [WeatherStation(code="001", name="Station1", lat=10.0, long=20.0)]

    ecmwf = make_ecmwf(staging, runs, stations)
    ecmwf.process_model_run(0)

    # For a single hour (0) get all the forecast hours (len(range(0, 145, 3)) + len(range(150, 241, 6))
    assert ecmwf.files_downloaded == expected_processed
    assert ecmwf.files_processed == expected_processed
    assert len(staging.processed_sources(RUN_TS)) == expected_processed
    assert ecmwf.complete_runs == expected_complete


def test_ecmwf_process_model_reprocesses_interrupted_publish(
    mocker, mock_herbie_instance, mock_forecast_processing, staging, runs
):
    """A run in `runs` that still has `staging` was interrupted while publishing: it is
    complete again without downloading anything, so it is published again."""
    publish(runs, RUN_TS)
    stage_hours(staging, RUN_TS, get_ecmwf_forecast_hours())
    process_forecast = mocker.spy(ECMWF, "_process_forecast_with_retry")

    ecmwf = make_ecmwf(staging, runs)
    ecmwf.process_model_run(0)

    process_forecast.assert_not_called()
    assert ecmwf.files_downloaded == 0
    assert ecmwf.files_processed == num_forecast_hours
    assert ecmwf.complete_runs == [RUN_TS]


def test_ecmwf_process_model_previously_partial_processed(
    mocker, mock_herbie_instance, mock_forecast_processing, staging, runs
):
    previously_processed = 3
    stage_hours(staging, RUN_TS, list(get_ecmwf_forecast_hours())[:previously_processed])
    process_forecast = mocker.spy(ECMWF, "_process_forecast_with_retry")

    ecmwf = make_ecmwf(staging, runs, [WeatherStation(code="001", name="S", lat=10.0, long=20.0)])
    ecmwf.process_model_run(0)

    assert ecmwf.files_processed == num_forecast_hours
    assert process_forecast.call_count == num_forecast_hours - previously_processed
    assert len(staging.processed_sources(RUN_TS)) == num_forecast_hours
    assert ecmwf.complete_runs == [RUN_TS]


def test_ecmwf_process_model_partial_process(
    mock_herbie_instance, mock_forecast_processing, staging, runs
):
    urls = ["url0", "url1", "url2"]
    unprocessed_urls = [None] * (num_forecast_hours - len(urls))
    type(mock_herbie_instance).grib = PropertyMock(side_effect=urls + unprocessed_urls)

    ecmwf = make_ecmwf(staging, runs, [WeatherStation(code="001", name="S", lat=10.0, long=20.0)])
    ecmwf.process_model_run(0)

    assert ecmwf.files_processed == len(urls)
    # the files processed before the missing one are staged for the next run to resume from
    assert staging.processed_sources(RUN_TS) == {
        forecast_hour_source(hour) for hour in list(get_ecmwf_forecast_hours())[: len(urls)]
    }
    assert ecmwf.complete_runs == []


def test_ecmwf_process(mock_herbie_instance, mock_forecast_processing, staging, runs):
    stations = [WeatherStation(code="001", name="Station1", lat=10.0, long=20.0)]
    ecmwf = make_ecmwf(staging, runs, stations)
    ecmwf.process()

    assert ecmwf.complete_runs == [
        datetime(2026, 11, 12, 0, tzinfo=timezone.utc),
        datetime(2026, 11, 12, 12, tzinfo=timezone.utc),
        datetime(2026, 11, 13, 0, tzinfo=timezone.utc),
        datetime(2026, 11, 13, 12, tzinfo=timezone.utc),
    ]
    # counters describe the most recently processed model run rather than accumulating across runs
    assert ecmwf.files_downloaded == num_forecast_hours
    assert ecmwf.files_processed == num_forecast_hours
    assert ecmwf.exception_count == 0


@pytest.mark.parametrize(
    "now, yesterday",
    [
        (
            datetime(2026, 11, 13, 0, 30, tzinfo=timezone.utc),
            datetime(2026, 11, 12, tzinfo=timezone.utc),
        ),
        (
            datetime(2026, 3, 1, 0, 30, tzinfo=timezone.utc),
            datetime(2026, 2, 28, tzinfo=timezone.utc),
        ),
        (
            datetime(2026, 1, 1, 0, 30, tzinfo=timezone.utc),
            datetime(2025, 12, 31, tzinfo=timezone.utc),
        ),
    ],
)
def test_ecmwf_process_resumes_previous_day_after_midnight(mocker, staging, runs, now, yesterday):
    previous_run_time = yesterday.replace(hour=12)
    publish(runs, yesterday)
    publish(runs, now.replace(hour=0, minute=0))
    stage_hours(staging, previous_run_time, [0])
    herbie = mocker.patch(
        "weather_model_jobs.ecmwf.Herbie",
        side_effect=[MagicMock(grib="pending", SOURCES={"mock": "pending"})],
    )
    mocker.patch(
        "weather_model_jobs.ecmwf.get_ecmwf_forecast_hours", side_effect=lambda: iter([0, 3])
    )
    ecmwf = make_ecmwf(staging, runs, now=now)
    process_forecast = mocker.patch.object(ecmwf, "_process_forecast_with_retry", return_value=[])

    ecmwf.process()

    assert [call.args[0] for call in herbie.call_args_list] == [
        previous_run_time.strftime("%Y-%m-%d %H")
    ]
    assert [call.kwargs["fxx"] for call in herbie.call_args_list] == [3]
    process_forecast.assert_called_once()
    model_info = process_forecast.call_args.args[1]
    assert model_info.model_run_timestamp == previous_run_time
    assert model_info.prediction_timestamp == previous_run_time + timedelta(hours=3)
    assert ecmwf.complete_runs == [previous_run_time]
    assert ecmwf.exception_count == 0


def test_ecmwf_process_skips_published_runs_without_downloads(mocker, staging, runs):
    for run_ts in [
        datetime(2026, 11, 12, 0, tzinfo=timezone.utc),
        datetime(2026, 11, 12, 12, tzinfo=timezone.utc),
        datetime(2026, 11, 13, 0, tzinfo=timezone.utc),
        datetime(2026, 11, 13, 12, tzinfo=timezone.utc),
    ]:
        publish(runs, run_ts)
    herbie = mocker.patch("weather_model_jobs.ecmwf.Herbie")
    ecmwf = make_ecmwf(staging, runs)

    ecmwf.process()

    herbie.assert_not_called()
    assert ecmwf.complete_runs == []
    assert not staging.exists()


def test_ecmwf_process_continues_after_unavailable_run(mocker, staging, runs):
    mocker.patch("weather_model_jobs.ecmwf.get_ecmwf_forecast_hours", side_effect=lambda: iter([0]))
    herbie = mocker.patch(
        "weather_model_jobs.ecmwf.Herbie",
        side_effect=[MagicMock(grib=None)]
        + [MagicMock(grib=f"url{index}", SOURCES={"mock": f"url{index}"}) for index in range(3)],
    )
    ecmwf = make_ecmwf(staging, runs)
    mocker.patch.object(ecmwf, "_process_forecast_with_retry", return_value=[])

    ecmwf.process()

    assert [call.args[0] for call in herbie.call_args_list] == [
        "2026-11-12 00",
        "2026-11-12 12",
        "2026-11-13 00",
        "2026-11-13 12",
    ]
    assert len(ecmwf.complete_runs) == 3
    assert ecmwf.exception_count == 0


def test_ecmwf_retries_503_with_backoff(mock_herbie_instance, mocker: MockerFixture, staging, runs):
    response = MagicMock(status_code=503)
    http_error = RuntimeError("503 Server Error: Slow Down")
    http_error.response = response
    wrapped_error = RuntimeError("Processing failed")
    wrapped_error.__cause__ = http_error

    mocker.patch("weather_model_jobs.ecmwf.get_ecmwf_forecast_hours", return_value=iter([0]))
    transformer = mocker.patch(
        "weather_model_jobs.ecmwf.get_ecmwf_transformer",
        side_effect=[wrapped_error, MagicMock()],
    )
    mocker.patch("weather_model_jobs.ecmwf.get_stations_dataframe", return_value=MagicMock())
    mocker.patch.object(ECMWFModelProcessor, "process_grib_data", return_value=MagicMock())
    mocker.patch("weather_model_jobs.ecmwf.station_values", return_value=[])
    mocker.patch("weather_model_jobs.ecmwf.random.uniform", return_value=0)
    sleep = mocker.patch("weather_model_jobs.ecmwf.time.sleep")
    stations = [WeatherStation(code="001", name="Station1", lat=10.0, long=20.0)]

    ecmwf = make_ecmwf(staging, runs, stations)
    ecmwf.process_model_run(0)

    assert transformer.call_count == 2
    sleep.assert_called_once_with(2)
    assert ecmwf.files_processed == 1
    assert ecmwf.exception_count == 0
    assert staging.processed_sources(RUN_TS) == {forecast_hour_source(0)}


def test_ecmwf_stops_retrying_503_after_max_retries(
    mock_herbie_instance, mocker: MockerFixture, caplog, staging, runs
):
    response = MagicMock(status_code=503)
    http_error = RuntimeError("503 Server Error: Slow Down")
    http_error.response = response
    wrapped_error = RuntimeError("Processing failed")
    wrapped_error.__cause__ = http_error

    mocker.patch("weather_model_jobs.ecmwf.get_ecmwf_forecast_hours", return_value=iter([0]))
    transformer = mocker.patch(
        "weather_model_jobs.ecmwf.get_ecmwf_transformer", side_effect=wrapped_error
    )
    mocker.patch("weather_model_jobs.ecmwf.random.uniform", return_value=0)
    sleep = mocker.patch("weather_model_jobs.ecmwf.time.sleep")
    stations = [WeatherStation(code="001", name="Station1", lat=10.0, long=20.0)]

    ecmwf = make_ecmwf(staging, runs, stations)
    ecmwf.process_model_run(0)

    assert transformer.call_count == 4
    assert [call.args[0] for call in sleep.call_args_list] == [2, 4, 8]
    assert ecmwf.files_processed == 0
    assert ecmwf.exception_count == 1
    assert staging.processed_sources(RUN_TS) == set()
    assert ecmwf.complete_runs == []
    assert "ECMWF forecast /path/to/mock/file.grib failed after 3 retries: HTTP 503" in caplog.text


def test_ecmwf_process_model_run_exception(
    mock_herbie_instance, mocker: MockerFixture, staging, runs
):
    mocker.patch(
        "weather_model_jobs.ecmwf.get_ecmwf_transformer",
        side_effect=Exception("test exception"),
    )
    stations = [WeatherStation(code="001", name="Station1", lat=10.0, long=20.0)]

    ecmwf = make_ecmwf(staging, runs, stations)
    ecmwf.process()

    assert ecmwf.complete_runs == []
    assert ecmwf.exception_count == (num_forecast_hours * 4)


def make_process_result(prediction_timestamp, data: xr.Dataset):
    process_result = MagicMock()
    process_result.model_run_info.prediction_timestamp = prediction_timestamp
    process_result.data = data
    return process_result


def test_station_values():
    prediction_timestamp = datetime(2025, 5, 1, 12, tzinfo=timezone.utc)
    process_result = make_process_result(
        prediction_timestamp,
        xr.Dataset(
            {
                "tmp_tgl_2": ("point_code", [25.0, 26.0]),
                "rh_tgl_2": ("point_code", [60.0, 61.0]),
                "not_a_model_field": ("point_code", [1.0, 1.0]),
            },
            coords={"point_code": [1, 2]},
        ),
    )
    stations = [
        WeatherStation(code=1, name="Station1", lat=10.0, long=20.0),
        WeatherStation(code=2, name="Station2", lat=15.0, long=25.0),
    ]

    values = station_values(stations, process_result)

    assert sorted(values) == sorted(
        [
            (1, prediction_timestamp, "tmp_tgl_2", 25.0),
            (1, prediction_timestamp, "rh_tgl_2", 60.0),
            (2, prediction_timestamp, "tmp_tgl_2", 26.0),
            (2, prediction_timestamp, "rh_tgl_2", 61.0),
        ]
    )


def test_station_values_handles_nan():
    prediction_timestamp = datetime(2024, 6, 1, 12, tzinfo=timezone.utc)
    process_result = make_process_result(
        prediction_timestamp,
        xr.Dataset(
            {
                "tmp_tgl_2": ("point_code", [22.5, 22.5]),
                "rh_tgl_2": ("point_code", [55.0, 55.0]),
                "wdir_tgl_10": ("point_code", [np.nan, np.nan]),
            },
            coords={"point_code": [1, 2]},
        ),
    )
    stations = [
        WeatherStation(code=1, name="Station1", lat=10.0, long=20.0),
        WeatherStation(code=2, name="Station2", lat=15.0, long=25.0),
    ]

    values = station_values(stations, process_result)

    by_variable = {(code, variable): value for code, _, variable, value in values}
    for code in (1, 2):
        assert by_variable[(code, "tmp_tgl_2")] == pytest.approx(22.5)
        assert by_variable[(code, "rh_tgl_2")] == pytest.approx(55.0)
        # NaN becomes a missing value
        assert by_variable[(code, "wdir_tgl_10")] is None


def test_ecmwf_process_handles_exceptions(mocker, caplog, staging, runs):
    stations = [WeatherStation(code="001", name="Station1", lat=10.0, long=20.0)]
    ecmwf = make_ecmwf(staging, runs, stations)
    process_run = mocker.patch.object(
        ecmwf, "process_model_run", side_effect=[RuntimeError("Mocked exception"), None, None, None]
    )
    ecmwf.process()

    assert process_run.call_args_list == [
        mocker.call(0, days_ago=1),
        mocker.call(12, days_ago=1),
        mocker.call(0, days_ago=0),
        mocker.call(12, days_ago=0),
    ]
    assert ecmwf.exception_count == 1
    assert "model run 2026-11-12 00:00 UTC" in caplog.text


def test_main_success(mocker: MockerFixture, monkeypatch):
    """Test the main function when it runs successfully."""
    mock_process_models = AsyncMock()

    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    monkeypatch.setattr(weather_model_jobs.ecmwf, "process_models", mock_process_models)
    mocker.patch.object(weather_model_jobs.ecmwf, "exit_process", side_effect=raise_system_exit)
    chatops_spy = mocker.spy(weather_model_jobs.ecmwf, "send_chatops_notification")

    with pytest.raises(SystemExit) as excinfo:
        weather_model_jobs.ecmwf.main()

    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_OK
    # Assert that rocket chat was called.
    assert chatops_spy.call_count == 0


def test_main_fail(mocker: MockerFixture, monkeypatch):
    """Run the main method, check that message is sent to rocket chat, and exit code is EX_SOFTWARE"""

    def mock_process_models():
        raise Exception()

    chatops_spy = mocker.spy(weather_model_jobs.ecmwf, "send_chatops_notification")
    monkeypatch.setattr(weather_model_jobs.ecmwf, "process_models", mock_process_models)
    mocker.patch.object(weather_model_jobs.ecmwf, "exit_process", side_effect=raise_system_exit)

    with pytest.raises(SystemExit) as excinfo:
        weather_model_jobs.ecmwf.main()

    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_SOFTWARE
    # Assert that rocket chat was called.
    assert chatops_spy.call_count == 1


@pytest.mark.anyio
async def test_process_models_filters_stations_to_crop_bounds(mocker: MockerFixture):
    station_coordinates = [
        (50.0, -120.0),
        (BC_MIN_LATITUDE, BC_MIN_LONGITUDE),
        (BC_MIN_LATITUDE, BC_MAX_LONGITUDE),
        (BC_MAX_LATITUDE, BC_MIN_LONGITUDE),
        (BC_MAX_LATITUDE, BC_MAX_LONGITUDE),
        (BC_MIN_LATITUDE - 0.1, -120.0),
        (BC_MAX_LATITUDE + 0.1, -120.0),
        (50.0, BC_MIN_LONGITUDE - 0.1),
        (50.0, BC_MAX_LONGITUDE + 0.1),
    ]
    stations = [
        WeatherStation(code=code, name=f"Station{code}", lat=latitude, long=longitude)
        for code, (latitude, longitude) in enumerate(station_coordinates, start=1)
    ]
    expected_stations = stations[:5]
    mock_temp_dir = MagicMock()
    mock_temp_dir.return_value.__enter__.return_value = "/mock/temp/dir"
    mocker.patch("weather_model_jobs.ecmwf.tempfile.TemporaryDirectory", mock_temp_dir)
    mocker.patch("weather_model_jobs.ecmwf.get_stations_asynchronously", return_value=stations)
    mock_ecmwf = mocker.patch("weather_model_jobs.ecmwf.ECMWF")
    mock_prediction_processor = mocker.patch("weather_model_jobs.ecmwf.ECMWFPredictionProcessor")

    await weather_model_jobs.ecmwf.process_models()

    mock_ecmwf.assert_called_once_with("/mock/temp/dir", expected_stations)
    mock_prediction_processor.assert_called_once_with(expected_stations)
    mock_ecmwf.return_value.process.assert_called_once()
    # only the runs the download fully staged are published
    mock_prediction_processor.return_value.process.assert_called_once_with(
        mock_ecmwf.return_value.complete_runs
    )


@pytest.mark.anyio
@pytest.mark.parametrize("coordinates", [[], [(BC_MIN_LATITUDE - 0.1, -120.0)]])
async def test_process_models_skips_when_no_stations_within_bounds(mocker, coordinates):
    stations = [
        WeatherStation(code=code, name=f"Station{code}", lat=latitude, long=longitude)
        for code, (latitude, longitude) in enumerate(coordinates, start=1)
    ]
    mocker.patch("weather_model_jobs.ecmwf.get_stations_asynchronously", return_value=stations)
    mock_ecmwf = mocker.patch("weather_model_jobs.ecmwf.ECMWF")
    mock_prediction_processor = mocker.patch("weather_model_jobs.ecmwf.ECMWFPredictionProcessor")

    await weather_model_jobs.ecmwf.process_models()

    mock_ecmwf.assert_not_called()
    mock_prediction_processor.assert_not_called()


def test_process_model_run_future_model_datetime(mocker, staging, runs):
    stations = [WeatherStation(code="001", name="Station1", lat=10.0, long=20.0)]
    herbie = mocker.patch("weather_model_jobs.ecmwf.Herbie")

    # fixed_now is 10:00, so 12:00 is in the future
    ecmwf = make_ecmwf(staging, runs, stations, now=datetime(2024, 6, 1, 10, tzinfo=timezone.utc))
    logger_spy = mocker.spy(weather_model_jobs.ecmwf.logger, "info")

    ecmwf.process_model_run(12)

    assert ecmwf.files_downloaded == 0
    assert ecmwf.files_processed == 0
    herbie.assert_not_called()
    assert ecmwf.complete_runs == []
    assert any(
        "is in the future. Exiting model run." in str(call.args[0])
        for call in logger_spy.call_args_list
    )


def test_expected_runs_are_the_runs_the_job_processes(mocker, staging, runs):
    ecmwf = ECMWF("/mock/temp/dir", [], staging_table=staging, runs_table=runs)
    process_model_run = mocker.patch.object(ecmwf, "process_model_run")

    ecmwf.process()

    processed = [
        ecmwf._run_ts(c.args[0], c.kwargs["days_ago"]) for c in process_model_run.call_args_list
    ]
    expected = list(ecmwf.expected_runs())
    assert [run_ts for run_ts, _ in expected] == processed
    hours = list(get_ecmwf_forecast_hours())
    assert all(sources == [f"fxx={hour:03d}" for hour in hours] for _, sources in expected)


@pytest.mark.anyio
async def test_staged_runs_are_published_before_anything_is_downloaded(mocker):
    calls = []
    station = WeatherStation(code=1, name="Station1", lat=50.0, long=-120.0)
    mocker.patch("weather_model_jobs.ecmwf.get_stations_asynchronously", return_value=[station])
    mocker.patch("weather_model_jobs.ecmwf.ECMWFPredictionProcessor")
    mocker.patch(
        "weather_model_jobs.ecmwf.publish_staged_runs",
        side_effect=lambda *args: calls.append("publish"),
    )
    ecmwf = mocker.patch("weather_model_jobs.ecmwf.ECMWF")
    ecmwf.return_value.process.side_effect = lambda: calls.append("download")

    await weather_model_jobs.ecmwf.process_models()

    assert calls == ["publish", "download"]
