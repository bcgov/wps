import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest
import weather_model_jobs.ecmwf
import wps_nwp as nwp
from aiohttp import ClientSession
from pytest_mock import MockerFixture
from weather_model_jobs import ModelEnum, ModelRunInfo, ModelRunProcessResult
from weather_model_jobs.ecmwf import (
    ECMWF,
    get_ecmwf_forecast_hours,
    get_forecast_url,
    get_model_run_hours,
)
from weather_model_jobs.ecmwf_model_processor import VARIABLES
from weather_model_jobs.utils.process_grib import PredictionModelNotFound
from wps_shared.db.crud.model_run_repository import ModelRunRepository
from wps_shared.db.models.weather_models import PredictionModelRunTimestamp
from wps_shared.schemas.stations import WeatherStation
from wps_shared.tests.common import default_mock_client_get

forecast_hours = list(get_ecmwf_forecast_hours())
num_forecast_hours = len(forecast_hours)


def raise_system_exit(code: int):
    raise SystemExit(code)


class FakeClient:
    """
    Stands in for nwp.Client.

    Streams a set of fields for each forecast hour it is asked for that is in published
    (every hour, if published is None), then raises error if one was given.
    """

    def __init__(self, published=None, variables=VARIABLES, error: Exception | None = None):
        self.published = published
        self.variables = variables
        self.error = error
        self.requests = []

    async def stream(self, model, run, steps, variables, *, skip_missing=False):
        steps = list(steps)
        self.requests.append((model, run, steps, tuple(variables), skip_missing))
        for step in steps:
            if self.published is None or step in self.published:
                yield [nwp.Field("ifs", v, run, step, "url", b"") for v in self.variables]
        if self.error:
            raise self.error


@pytest.fixture
def mock_stations():
    return [
        WeatherStation(code="001", name="Station1", lat=10.0, long=20.0),
        WeatherStation(code="002", name="Station2", lat=15.0, long=25.0),
    ]


@pytest.fixture(autouse=True)
def mock_station_values(mocker: MockerFixture):
    """Decoding is covered by the processor's own tests; here every hour yields no values."""
    return mocker.patch("weather_model_jobs.ecmwf.station_values", AsyncMock(return_value={}))


class MockModelRunRepository(ModelRunRepository):
    def __init__(self):
        self.get_or_create_prediction_run_calls = 0
        self.prediction_runs = {}
        self.session = MagicMock()
        # Mock methods for call tracking in tests
        self.get_model_run_prediction = MagicMock()
        self.store_model_run_prediction = MagicMock()
        self.mark_prediction_model_run_processed = MagicMock()
        self.mark_url_as_processed = MagicMock()

    def get_prediction_model(self, _, __):
        return ModelEnum.ECMWF

    def get_or_create_prediction_run(self, prediction_model, prediction_run_timestamp):
        self.get_or_create_prediction_run_calls += 1
        key = (prediction_model, prediction_run_timestamp)
        if key not in self.prediction_runs:
            run = MagicMock()
            run.complete = False
            self.prediction_runs[key] = run
        return self.prediction_runs[key]

    def get_processed_url(self, url):
        return None


def mock_repository(complete: bool = False) -> MagicMock:
    repository = MagicMock(spec=ModelRunRepository)
    repository.session = MagicMock()
    repository.get_or_create_prediction_run.return_value.complete = complete
    repository.get_processed_url.return_value = None
    return repository


def test_get_model_run_hours():
    hours = list(get_model_run_hours(ModelEnum.ECMWF))
    assert hours == [0, 12]


def test_get_ecmwf_forecast_hours():
    hours = list(get_ecmwf_forecast_hours())
    assert hours[:5] == [0, 3, 6, 9, 12]
    assert hours[-5:] == [216, 222, 228, 234, 240]


def test_get_forecast_url():
    # Hours already processed are recorded in the database under this address, so it must
    # not change: if it did, every hour of the runs in progress would be processed again.
    url = get_forecast_url(datetime(2024, 10, 10, 12, tzinfo=timezone.utc), 3)

    assert url == (
        "https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/"
        "20241010/12z/ifs/0p25/oper/20241010120000-3h-oper-fc.grib2"
    )


@pytest.mark.anyio
async def test_ecmwf_process_model_run_nothing_published(mock_stations):
    repository = mock_repository()
    ecmwf = ECMWF(FakeClient(published=set()), mock_stations, repository)

    await ecmwf.process_model_run(0)

    assert ecmwf.files_downloaded == 0
    assert ecmwf.files_processed == 0
    repository.mark_prediction_model_run_processed.assert_not_called()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "complete, expected_processed, expected_complete",
    [(False, num_forecast_hours, 1), (True, 0, 0)],
)
async def test_ecmwf_process_model_complete(
    complete, expected_processed, expected_complete, mock_stations
):
    repository = mock_repository(complete)
    client = FakeClient()

    ecmwf = ECMWF(client, mock_stations, repository)
    await ecmwf.process_model_run(0)

    # For a single hour (0) get all the forecast hours (len(range(0, 145, 3)) + len(range(150, 241, 6))
    assert ecmwf.files_downloaded == expected_processed
    assert ecmwf.files_processed == expected_processed
    assert repository.mark_url_as_processed.call_count == expected_processed
    assert repository.mark_prediction_model_run_processed.call_count == expected_complete
    assert len(client.requests) == (0 if complete else 1)


@pytest.mark.anyio
async def test_ecmwf_requests_every_hour_of_the_run_and_tolerates_unpublished_ones(mock_stations):
    client = FakeClient()
    ecmwf = ECMWF(client, mock_stations, mock_repository())

    await ecmwf.process_model_run(12)

    model_datetime = ecmwf.now.replace(hour=12, minute=0, second=0, microsecond=0)
    assert client.requests == [(nwp.IFS, model_datetime, forecast_hours, VARIABLES, True)]


@pytest.mark.anyio
async def test_ecmwf_records_each_hour_under_its_own_url(mock_stations):
    repository = mock_repository()
    ecmwf = ECMWF(FakeClient(published={0, 6, 240}), mock_stations, repository)

    await ecmwf.process_model_run(0)

    model_datetime = ecmwf.now.replace(hour=0, minute=0, second=0, microsecond=0)
    recorded = {call.args[0] for call in repository.mark_url_as_processed.call_args_list}
    assert recorded == {get_forecast_url(model_datetime, hour) for hour in (0, 6, 240)}


@pytest.mark.anyio
async def test_ecmwf_process_model_previously_partial_processed(mock_stations):
    repository = mock_repository()
    processed_urls = ["url0", "url1", "url2"]
    unprocessed_urls = [None] * (num_forecast_hours - len(processed_urls))
    repository.get_processed_url.side_effect = processed_urls + unprocessed_urls
    client = FakeClient()

    ecmwf = ECMWF(client, mock_stations, repository)
    await ecmwf.process_model_run(0)

    assert ecmwf.files_processed == num_forecast_hours
    assert ecmwf.files_downloaded == num_forecast_hours - len(processed_urls)
    assert repository.mark_url_as_processed.call_count == num_forecast_hours - len(processed_urls)
    assert repository.mark_prediction_model_run_processed.call_count == 1
    # hours that were processed on an earlier run are not fetched again
    assert client.requests[0][2] == forecast_hours[len(processed_urls) :]


@pytest.mark.anyio
async def test_ecmwf_process_model_partial_process(mock_stations):
    repository = mock_repository()
    published = forecast_hours[:3]

    ecmwf = ECMWF(FakeClient(published=published), mock_stations, repository)
    await ecmwf.process_model_run(0)

    assert ecmwf.files_processed == len(published)
    assert repository.mark_url_as_processed.call_count == len(published)
    assert repository.mark_prediction_model_run_processed.call_count == 0


@pytest.mark.anyio
async def test_ecmwf_leaves_an_hour_with_variables_missing_for_a_later_run(
    mock_stations, mock_station_values
):
    repository = mock_repository()

    ecmwf = ECMWF(FakeClient(variables=VARIABLES[:-1]), mock_stations, repository)
    await ecmwf.process_model_run(0)

    assert ecmwf.files_downloaded == 0
    assert ecmwf.files_processed == 0
    mock_station_values.assert_not_called()
    repository.mark_url_as_processed.assert_not_called()


@pytest.mark.anyio
async def test_ecmwf_process(mock_stations):
    mock_repo = MockModelRunRepository()
    ecmwf = ECMWF(FakeClient(), mock_stations, mock_repo)

    await ecmwf.process()

    assert mock_repo.get_or_create_prediction_run_calls == 2  # For hours 0 and 12
    # counters describe the most recently processed model run rather than accumulating across runs
    assert ecmwf.files_downloaded == num_forecast_hours
    assert ecmwf.files_processed == num_forecast_hours
    assert ecmwf.exception_count == 0


@pytest.mark.anyio
async def test_ecmwf_process_model_run_exception(mock_stations, mock_station_values):
    mock_station_values.side_effect = Exception("test exception")
    mock_repo = MockModelRunRepository()

    ecmwf = ECMWF(FakeClient(), mock_stations, mock_repo)
    await ecmwf.process()

    # every hour of both runs fails on its own, and the others are still attempted
    assert ecmwf.exception_count == (num_forecast_hours * 2)
    assert ecmwf.files_processed == 0
    assert mock_repo.session.rollback.call_count == num_forecast_hours * 2
    mock_repo.mark_url_as_processed.assert_not_called()
    mock_repo.mark_prediction_model_run_processed.assert_not_called()


@pytest.mark.anyio
async def test_ecmwf_download_failure_ends_the_run_but_keeps_what_was_processed(mock_stations):
    repository = mock_repository()
    failure = nwp.FetchError("https://mirror.test/file.grib2", "HTTP 503", 503)
    client = FakeClient(published=forecast_hours[:2], error=failure)

    ecmwf = ECMWF(client, mock_stations, repository)
    await ecmwf.process()

    # one failure for each of the two model runs, each after two hours had been stored
    assert ecmwf.exception_count == 2
    assert repository.mark_url_as_processed.call_count == 4
    repository.mark_prediction_model_run_processed.assert_not_called()


@pytest.mark.anyio
async def test_process_forecast_stores_values_for_the_hour(mock_stations, mock_station_values):
    run = datetime(2024, 10, 10, 12, tzinfo=timezone.utc)
    mock_station_values.return_value = {"tmp_tgl_2": np.array([1.0, 2.0])}
    fields = [nwp.Field("ifs", variable, run, 6, "url", b"") for variable in VARIABLES]
    ecmwf = ECMWF(FakeClient(), mock_stations, mock_repository())
    store = MagicMock()
    ecmwf.store_processed_result = store

    await ecmwf._process_forecast(fields, "the url", "the prediction run")

    (prediction_run, result), _ = store.call_args
    assert prediction_run == "the prediction run"
    assert result.url == "the url"
    assert result.data == mock_station_values.return_value
    assert result.model_run_info.model_run_timestamp == run
    assert result.model_run_info.prediction_timestamp == datetime(
        2024, 10, 10, 18, tzinfo=timezone.utc
    )
    (sampled_fields, lats, lons), _ = mock_station_values.call_args
    assert sampled_fields == fields
    assert (list(lats), list(lons)) == ([10.0, 15.0], [20.0, 25.0])


def process_result(data: dict) -> ModelRunProcessResult:
    model_run_info = ModelRunInfo(prediction_timestamp="2025-05-01T12:00:00Z")
    return ModelRunProcessResult(model_run_info=model_run_info, url="url", data=data)


@pytest.mark.parametrize(
    "prediction_exists",
    [(True), (False)],
)
def test_store_processed_result(prediction_exists, mock_stations):
    mock_repo = MagicMock(spec=ModelRunRepository)
    if prediction_exists:
        # a different existing prediction for each station
        mock_repo.get_model_run_prediction.side_effect = lambda *_: MagicMock()
    else:
        mock_repo.get_model_run_prediction.return_value = None
    mock_prediction_run = MagicMock(spec=PredictionModelRunTimestamp)
    mock_prediction_run.id = 1
    result = process_result(
        {"tmp_tgl_2": np.array([25.0, 26.0]), "rh_tgl_2": np.array([60.0, 61.0])}
    )

    ecmwf = ECMWF(FakeClient(), mock_stations, mock_repo)
    ecmwf.store_processed_result(mock_prediction_run, result)

    assert mock_repo.get_model_run_prediction.call_count == len(mock_stations)
    assert mock_repo.store_model_run_prediction.call_count == len(mock_stations)
    # each station gets the value at its own position
    stored = [call.args[0] for call in mock_repo.store_model_run_prediction.call_args_list]
    assert [(p.tmp_tgl_2, p.rh_tgl_2) for p in stored] == [(25.0, 60.0), (26.0, 61.0)]
    if not prediction_exists:
        assert [p.station_code for p in stored] == [s.code for s in mock_stations]
        assert all(p.prediction_model_run_timestamp_id == 1 for p in stored)
        assert all(p.prediction_timestamp == "2025-05-01T12:00:00Z" for p in stored)


def test_store_processed_result_handles_nan(mock_stations):
    mock_prediction_run = MagicMock(spec=PredictionModelRunTimestamp)
    mock_repo = MockModelRunRepository()
    result = process_result(
        {
            "tmp_tgl_2": np.array([22.5, 22.5]),
            "rh_tgl_2": np.array([55.0, 55.0]),
            "wdir_tgl_10": np.array([np.nan, np.nan]),
        }
    )

    ecmwf = ECMWF(FakeClient(), mock_stations, mock_repo)
    ecmwf.store_processed_result(mock_prediction_run, result)

    # should call get_model_run_prediction and store_model_run_prediction for each station
    assert mock_repo.get_model_run_prediction.call_count == len(mock_stations)
    assert mock_repo.store_model_run_prediction.call_count == len(mock_stations)

    # check that temperature and rh are set, wind dir is None due to NaN
    for call in mock_repo.store_model_run_prediction.call_args_list:
        prediction = call.args[0]

        assert prediction.tmp_tgl_2 == pytest.approx(22.5)
        assert prediction.rh_tgl_2 == pytest.approx(55.0)
        assert prediction.wdir_tgl_10 is None


@pytest.mark.anyio
async def test_ecmwf_process_handles_exceptions(mock_stations, monkeypatch):
    monkeypatch.setattr(
        ECMWF, "process_model_run", AsyncMock(side_effect=Exception("Mocked exception"))
    )

    ecmwf = ECMWF(FakeClient(), mock_stations, MagicMock(spec=ModelRunRepository))
    await ecmwf.process()

    assert ecmwf.exception_count == 2  # one for each model run


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
async def test_process_models_success(mocker: MockerFixture, mock_stations):
    """Test process_models when it runs successfully."""
    mock_repo = MockModelRunRepository()
    mock_session_scope = MagicMock()
    mock_session_scope.return_value.__enter__.return_value = mock_repo
    mocker.patch("weather_model_jobs.ecmwf.get_stations_asynchronously", return_value=mock_stations)
    mocker.patch(
        "weather_model_jobs.ecmwf.get_write_session_scope", return_value=mock_session_scope
    )

    mock_ecmwf = mocker.patch("weather_model_jobs.ecmwf.ECMWF")
    mock_ecmwf_instance = mock_ecmwf.return_value
    mock_ecmwf_instance.process = AsyncMock()
    mock_ecmwf_instance.files_processed = 10

    await weather_model_jobs.ecmwf.process_models()

    mock_ecmwf_instance.process.assert_awaited_once()
    client, stations, _ = mock_ecmwf.call_args.args
    assert isinstance(client, nwp.Client)
    assert stations == mock_stations


@pytest.mark.anyio
async def test_process_model_run_prediction_model_not_found(mock_stations):
    """Test process_model_run when prediction model is not found."""
    mock_repo = MockModelRunRepository()
    mock_repo.get_prediction_model = MagicMock(
        return_value=None
    )  # Simulate missing prediction model
    ecmwf = ECMWF(FakeClient(), mock_stations, mock_repo)

    with pytest.raises(PredictionModelNotFound):
        await ecmwf.process_model_run(0)

    assert ecmwf.files_downloaded == 0
    assert ecmwf.files_processed == 0
    assert ecmwf.exception_count == 0


@pytest.mark.anyio
@pytest.mark.parametrize(
    "complete",
    [(True), (False)],
)
async def test_process_model_run_prediction_model_complete(mock_stations, complete):
    """Test process_model_run when the prediction run is, or is not, already complete."""
    mock_repo = MockModelRunRepository()
    mock_prediction_run = MagicMock(spec=PredictionModelRunTimestamp)
    mock_prediction_run.complete = complete
    mock_repo.get_or_create_prediction_run = MagicMock(return_value=mock_prediction_run)
    ecmwf = ECMWF(FakeClient(published=set()), mock_stations, mock_repo)

    await ecmwf.process_model_run(0)

    assert ecmwf.files_downloaded == 0
    assert ecmwf.files_processed == 0
    assert ecmwf.exception_count == 0
    assert len(ecmwf.client.requests) == (0 if complete else 1)


@pytest.mark.anyio
async def test_process_model_run_future_model_datetime(mocker, mock_stations):
    mock_repo = MagicMock(spec=ModelRunRepository)

    # set a fixed 'now' and patch time_utils.get_utc_now
    fixed_now = datetime(2024, 6, 1, 10, 0, 0)
    mocker.patch("weather_model_jobs.ecmwf.time_utils.get_utc_now", return_value=fixed_now)

    ecmwf = ECMWF(FakeClient(), mock_stations, mock_repo)
    logger_spy = mocker.spy(weather_model_jobs.ecmwf.logger, "info")

    future_hour = 12  # fixed_now is 10:00, so 12:00 is in the future

    await ecmwf.process_model_run(future_hour)

    assert ecmwf.files_downloaded == 0
    assert ecmwf.files_processed == 0

    mock_repo.get_prediction_model.assert_not_called()
    mock_repo.get_or_create_prediction_run.assert_not_called()

    assert any(
        "is in the future. Exiting model run." in str(call.args[0])
        for call in logger_spy.call_args_list
    )
