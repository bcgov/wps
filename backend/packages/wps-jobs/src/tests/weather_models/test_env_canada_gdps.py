"""Unit tests for app/env_canada.py"""

import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
import requests
import wps_shared.utils.time as time_utils
from aiohttp import ClientSession
from tests.weather_models.test_models_common import (
    MockResponse,
    mock_get_stations,
)
from weather_model_jobs import common_model_fetchers, env_canada
from weather_model_jobs.common_model_fetchers import RunStager
from wps_shared.tests.common import default_mock_client_get
from wps_shared.weather_models import (
    ModelEnum,
    NoFilesProcessed,
)
from wps_weather_data.runs import RunsTable
from wps_weather_data.staging import StagedFile, StagingTable

logger = logging.getLogger(__name__)


@pytest.mark.parametrize("model_run_hour", [0, 6, 12, 18])
def test_no_files_warning_is_due_n_hours_after_model_run(model_run_hour: int):
    model_run = datetime(2026, 6, 2, model_run_hour, tzinfo=timezone.utc)

    assert not env_canada.is_no_files_warning_due(
        model_run,
        model_run + env_canada.NO_FILES_WARNING_DELAY - timedelta(minutes=1),
        model_run_hour,
    )
    assert env_canada.is_no_files_warning_due(
        model_run,
        model_run + env_canada.NO_FILES_WARNING_DELAY,
        model_run_hour,
    )


def test_no_files_warning_uses_the_run_targeted_when_the_job_started():
    job_started = datetime(2026, 6, 2, 17, tzinfo=timezone.utc)
    job_finished = datetime(2026, 6, 2, 18, 30, tzinfo=timezone.utc)

    assert env_canada.is_no_files_warning_due(job_started, job_finished, 12)


@pytest.mark.parametrize(
    ("complete", "elapsed", "expected_overdue"),
    [
        (True, env_canada.NO_FILES_WARNING_DELAY, False),
        (False, env_canada.NO_FILES_WARNING_DELAY - timedelta(minutes=1), False),
        (False, env_canada.NO_FILES_WARNING_DELAY, True),
    ],
)
def test_model_run_must_be_incomplete_and_past_warning_delay_to_warn(
    monkeypatch: pytest.MonkeyPatch,
    complete: bool,
    elapsed: timedelta,
    expected_overdue: bool,
):
    model_run = datetime(2026, 6, 2, 12, tzinfo=timezone.utc)
    warning_time = model_run + elapsed
    monkeypatch.setattr(time_utils, "get_utc_now", lambda: model_run)
    monkeypatch.setattr(env_canada, "GribFileProcessor", MagicMock)
    monkeypatch.setattr(env_canada, "get_model_run_urls", lambda *args: ["url"])
    monkeypatch.setattr(env_canada, "ECCCUrlFetcher", lambda *args: MagicMock())

    canada = env_canada.EnvCanada(ModelEnum.GDPS)

    def process_urls(urls, fetcher, stager):
        if complete:
            stager.add("url", model_run, [])

    canada.process_model_run_urls = process_urls
    monkeypatch.setattr(time_utils, "get_utc_now", lambda: warning_time)

    canada.process_model_run(12)

    assert canada.has_overdue_incomplete_model_run is expected_overdue
    assert canada.complete_runs == ([model_run] if complete else [])


def test_published_run_is_skipped(monkeypatch: pytest.MonkeyPatch):
    model_run = datetime(2026, 6, 2, 12, tzinfo=timezone.utc)
    monkeypatch.setattr(time_utils, "get_utc_now", lambda: model_run + timedelta(hours=1))
    monkeypatch.setattr(env_canada, "GribFileProcessor", MagicMock)
    monkeypatch.setattr(env_canada, "get_model_run_urls", lambda *args: ["url"])
    RunsTable().append_run(
        ModelEnum.GDPS, model_run, [{"station_code": 1, "prediction_timestamp": model_run}]
    )

    canada = env_canada.EnvCanada(ModelEnum.GDPS)
    canada.process_model_run_urls = MagicMock()
    canada.process_model_run(12)

    canada.process_model_run_urls.assert_not_called()
    assert canada.complete_runs == []


def test_interrupted_run_is_completed_again(monkeypatch: pytest.MonkeyPatch):
    """A run in `runs` that is still staged was interrupted while publishing."""
    model_run = datetime(2026, 6, 2, 12, tzinfo=timezone.utc)
    monkeypatch.setattr(time_utils, "get_utc_now", lambda: model_run + timedelta(hours=1))
    monkeypatch.setattr(env_canada, "GribFileProcessor", MagicMock)
    monkeypatch.setattr(env_canada, "get_model_run_urls", lambda *args: ["url"])
    monkeypatch.setattr(env_canada, "ECCCUrlFetcher", lambda *args: MagicMock())
    RunsTable().append_run(
        ModelEnum.GDPS, model_run, [{"station_code": 1, "prediction_timestamp": model_run}]
    )
    StagingTable(ModelEnum.GDPS).append_files(model_run, [StagedFile("url", model_run, [])])

    canada = env_canada.EnvCanada(ModelEnum.GDPS)
    canada.process_model_run(12)

    assert canada.complete_runs == [model_run]


@pytest.fixture()
def only_first_url_unprocessed(monkeypatch):
    """Every URL except the first one asked about counts as processed, so only one file is
    downloaded. Returns the URLs that were downloaded."""
    downloaded = []
    is_processed = RunStager.is_processed

    def first_url_only(self, source):
        if not downloaded:
            downloaded.append(source)
        return source not in downloaded or is_processed(self, source)

    monkeypatch.setattr(RunStager, "is_processed", first_url_only)
    return downloaded


@pytest.fixture()
def mock_download(monkeypatch):
    """fixture for env_canada.download"""

    def mock_requests_get_gdps(*args, **kwargs):
        """mock env_canada download method for GDPS"""
        dirname = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(
            dirname, "20260602T00Z_MSC_GDPS_AirTemp_AGL-2m_LatLon0.15_PT000H.grib2"
        )
        with open(filename, "rb") as file:
            content = file.read()
        return MockResponse(status_code=200, content=content)

    monkeypatch.setattr(requests.Session, "get", mock_requests_get_gdps)


@pytest.fixture()
def mock_download_fail(monkeypatch):
    """fixture for env_canada.download"""

    def mock_requests_get(*args, **kwargs):
        """mock env_canada download method"""
        return MockResponse(status_code=400)

    monkeypatch.setattr(requests, "get", mock_requests_get)


@pytest.fixture()
def mock_get_stations_synchronously(monkeypatch):
    monkeypatch.setattr(common_model_fetchers, "get_stations_synchronously", mock_get_stations)


def test_process_gdps(
    mock_download,
    only_first_url_unprocessed,
    mock_get_stations_synchronously,
    monkeypatch: pytest.MonkeyPatch,
):
    """run main method to see if it runs successfully."""
    # All files, except one, are treated as already processed, so we expect one file to be
    # processed and staged.
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    sys.argv = ["argv", "GDPS"]
    assert env_canada.process_models() == 1
    staged = {
        source
        for hour in (0, 12)
        for source in StagingTable(ModelEnum.GDPS).processed_sources(
            common_model_fetchers.model_run_timestamp(time_utils.get_utc_now(), hour)
        )
    }
    assert staged == set(only_first_url_unprocessed)


def test_connection_error_increments_connection_error_count_not_exception_count(monkeypatch):
    """Connection failures from the fetcher should not count as unexpected exceptions."""
    monkeypatch.setattr(env_canada, "GribFileProcessor", MagicMock)

    fetcher = MagicMock()
    fetcher.get.side_effect = requests.ConnectionError("HPFX and DD both unreachable")

    canada = env_canada.EnvCanada(ModelEnum.GDPS)
    stager = MagicMock()
    stager.is_processed.return_value = False
    canada.process_model_run_urls(
        [
            "https://dd.weather.gc.ca/today/model_gdps/15km/00/001/20260623T00Z_MSC_GDPS_AirTemp_AGL-2m_LatLon0.15_PT001H.grib2"
        ],
        fetcher,
        stager,
    )
    stager.add.assert_not_called()

    assert canada.connection_error_count == 1
    assert canada.exception_count == 0


def test_http_error_increments_exception_count_not_connection_error_count(monkeypatch):
    """HTTP errors (e.g. 503) from the fetcher are unexpected and must count as exceptions."""
    monkeypatch.setattr(env_canada, "GribFileProcessor", MagicMock)

    fetcher = MagicMock()
    fetcher.get.side_effect = requests.HTTPError("503 Server Error")

    canada = env_canada.EnvCanada(ModelEnum.GDPS)
    stager = MagicMock()
    stager.is_processed.return_value = False
    canada.process_model_run_urls(
        [
            "https://dd.weather.gc.ca/today/model_gdps/15km/00/001/20260623T00Z_MSC_GDPS_AirTemp_AGL-2m_LatLon0.15_PT001H.grib2"
        ],
        fetcher,
        stager,
    )
    stager.add.assert_not_called()

    assert canada.exception_count == 1
    assert canada.connection_error_count == 0


def test_process_models_does_not_raise_when_all_urls_already_processed(
    mock_get_stations_synchronously,
    monkeypatch: pytest.MonkeyPatch,
):
    """A clean re-run where all URLs are already staged should not fire NoFilesProcessed."""
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    # Every URL counts as staged, so all are skipped as already processed.
    monkeypatch.setattr(RunStager, "is_processed", lambda self, source: True)
    # Publishing is tested elsewhere; nothing here is really staged.
    monkeypatch.setattr(env_canada, "ModelValueProcessor", MagicMock())
    sys.argv = ["argv", "GDPS"]
    # Should complete without raising — returns 0 (nothing new to process).
    result = env_canada.process_models()
    assert result == 0


def test_process_models_raises_no_files_processed_when_all_downloads_fail(
    mock_get_stations_synchronously,
    monkeypatch: pytest.MonkeyPatch,
):
    """process_models() raises NoFilesProcessed when every download fails with a connection error."""
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    monkeypatch.setattr(requests.Session, "get", MagicMock(side_effect=requests.ConnectionError()))
    monkeypatch.setattr(
        time_utils,
        "get_utc_now",
        lambda: datetime(2026, 6, 2, 4, tzinfo=timezone.utc),
    )
    sys.argv = ["argv", "GDPS"]
    with pytest.raises(NoFilesProcessed):
        env_canada.process_models()


# The verdict rules themselves live on the shared runner and are tested in
# test_model_job_runner.py. All this job has to get right is the wiring.


@pytest.mark.parametrize("raise_on_no_files", [False, True])
def test_process_models_delegates_the_verdict_to_judge_run(
    monkeypatch: pytest.MonkeyPatch,
    raise_on_no_files: bool,
):
    """process_models() must hand its counters to judge_run and return the result."""
    monkeypatch.setattr(env_canada, "ModelValueProcessor", MagicMock())
    monkeypatch.setattr(env_canada, "GribFileProcessor", MagicMock())

    def finished_run(self):
        self.files_processed = 7
        self.connection_error_count = 2
        self.exception_count = 0
        self.has_overdue_incomplete_model_run = raise_on_no_files

    monkeypatch.setattr(env_canada.EnvCanada, "process", finished_run)
    judge_run = MagicMock(return_value=7)
    monkeypatch.setattr(env_canada, "judge_run", judge_run)
    monkeypatch.setattr(sys, "argv", ["argv", "GDPS"])

    assert env_canada.process_models() == 7

    job = judge_run.call_args.args[0]
    assert (job.files_processed, job.connection_error_count, job.exception_count) == (7, 2, 0)
    assert judge_run.call_args.kwargs == {
        "source": "Env Canada",
        "model": "GDPS",
        "raise_on_no_files": raise_on_no_files,
    }


def test_main_delegates_to_the_shared_runner(monkeypatch: pytest.MonkeyPatch):
    """main() must hand process_models to the runner, tagged with this job's source."""
    run_model_job = MagicMock()
    monkeypatch.setattr(env_canada, "run_model_job", run_model_job)
    monkeypatch.setattr(sys, "argv", ["argv", "GDPS"])

    env_canada.main()

    run_model_job.assert_called_once_with(
        env_canada.process_models, source="Env Canada", model="GDPS"
    )


def test_staged_runs_are_published_before_anything_is_downloaded(
    mock_get_stations_synchronously, monkeypatch: pytest.MonkeyPatch
):
    calls = []
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    monkeypatch.setattr(time_utils, "get_utc_now", lambda: datetime.now(timezone.utc))
    canada = env_canada.EnvCanada(ModelEnum.GDPS)
    run_ts, urls = next(iter(canada.expected_runs()))
    canada.staging_table.append_files(run_ts, [StagedFile(url, run_ts) for url in urls])
    publisher = MagicMock()
    publisher.process.side_effect = lambda runs: calls.append(("publish", list(runs)))
    monkeypatch.setattr(env_canada, "ModelValueProcessor", MagicMock(return_value=publisher))
    monkeypatch.setattr(env_canada.EnvCanada, "process", lambda self: calls.append("download"))
    sys.argv = ["argv", "GDPS"]

    env_canada.process_models()

    # Then whatever the downloads completed, here nothing.
    assert calls == [("publish", [run_ts]), "download", ("publish", [])]


def test_expected_runs_are_the_runs_and_files_the_job_downloads(
    mock_get_stations_synchronously, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    canada = env_canada.EnvCanada(ModelEnum.GDPS)
    stagers = []
    monkeypatch.setattr(
        canada,
        "process_model_run_urls",
        lambda urls, fetcher, stager: stagers.append((stager.run_ts, list(urls))),
    )

    canada.process()

    assert [(run_ts, list(urls)) for run_ts, urls in canada.expected_runs()] == stagers
