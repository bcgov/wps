"""Unit tests for app/env_canada.py"""

import logging
import os
import sys

import pytest
import requests
import wps_shared.db.crud.weather_models
import wps_shared.utils.time as time_utils
from aiohttp import ClientSession
from sqlalchemy.orm import Session
from tests.weather_models.crud import get_actuals_left_outer_join_with_predictions
from tests.weather_models.test_models_common import (
    MockResponse,
    mock_get_stations,
)
from unittest.mock import MagicMock

from weather_model_jobs import common_model_fetchers, env_canada, machine_learning
from wps_shared.db.models.weather_models import (
    PredictionModel,
    PredictionModelRunTimestamp,
    ProcessedModelRunUrl,
)
from wps_shared.tests.common import default_mock_client_get
from wps_shared.weather_models import (
    CompletedWithSomeExceptions,
    ModelEnum,
    NoFilesProcessed,
)

logger = logging.getLogger(__name__)


@pytest.fixture()
def mock_get_processed_file_record(monkeypatch):
    """Mock "get_processed_file_record" to only return the None on the 1st call."""
    called = False

    def get_processed_file_record(session: Session, url: str):
        nonlocal called
        if called:
            return ProcessedModelRunUrl()
        called = True
        return None

    monkeypatch.setattr(env_canada, "get_processed_file_record", get_processed_file_record)


@pytest.fixture()
def mock_get_actuals_left_outer_join_with_predictions(monkeypatch):
    """Mock out call to DB returning actuals macthed with predictions"""
    monkeypatch.setattr(
        machine_learning,
        "get_actuals_left_outer_join_with_predictions",
        get_actuals_left_outer_join_with_predictions,
    )


@pytest.fixture()
def mock_database(monkeypatch):
    """Mocked out database queries"""
    gdps_url = (
        "https://dd.weather.gc.ca/today/model_gdps/15km/00/000/"
        "20260602T00Z_MSC_GDPS_AirTemp_AGL-2m_LatLon0.15_PT000H.grib2"
    )
    gdps_processed_model_run = ProcessedModelRunUrl(url=gdps_url)
    gdps_prediction_model = PredictionModel(
        id=1,
        abbreviation="GDPS",
        projection="latlon.15x.15",
        name="Global Deterministic Prediction System",
    )
    gdps_prediction_model_run = PredictionModelRunTimestamp(
        id=1,
        prediction_model_id=1,
        prediction_run_timestamp=time_utils.get_utc_now(),
        prediction_model=gdps_prediction_model,
        complete=True,
    )

    def mock_get_gdps_prediction_model_run_timestamp_records(*args, **kwargs):
        return [(gdps_prediction_model_run, gdps_prediction_model)]

    def mock_get_processed_file_record(session, url: str):
        # We only want the one file to be processed - otherwise our test takes forever
        if url != gdps_url:
            return gdps_processed_model_run
        return None

    def mock_get_prediction_run(*args, **kwargs):
        return gdps_prediction_model_run

    monkeypatch.setattr(
        common_model_fetchers,
        "get_prediction_model_run_timestamp_records",
        mock_get_gdps_prediction_model_run_timestamp_records,
    )
    monkeypatch.setattr(
        common_model_fetchers, "get_processed_file_record", mock_get_processed_file_record
    )
    monkeypatch.setattr(
        wps_shared.db.crud.weather_models, "get_prediction_run", mock_get_prediction_run
    )


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
def mock_get_processed_file_count(monkeypatch):
    monkeypatch.setattr(
        wps_shared.db.crud.weather_models, "get_processed_file_count", mock_get_processed_file_count
    )


@pytest.fixture()
def mock_get_stations_synchronously(monkeypatch):
    monkeypatch.setattr(common_model_fetchers, "get_stations_synchronously", mock_get_stations)


@pytest.mark.usefixtures("mock_get_processed_file_record")
def test_process_gdps(
    mock_download,
    mock_database,
    mock_get_actuals_left_outer_join_with_predictions,
    mock_get_stations_synchronously,
    mock_get_processed_file_count,
    monkeypatch: pytest.MonkeyPatch,
):
    """run main method to see if it runs successfully."""
    # All files, except one, are marked as already having been downloaded, so we expect one file to
    # be processed.
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    sys.argv = ["argv", "GDPS"]
    assert env_canada.process_models() == 1


def test_connection_error_increments_connection_error_count_not_exception_count(monkeypatch):
    """Connection failures from the fetcher should not count as unexpected exceptions."""
    monkeypatch.setattr(env_canada, "GribFileProcessor", MagicMock)
    monkeypatch.setattr(env_canada, "get_processed_file_record", lambda session, url: None)

    fetcher = MagicMock()
    fetcher.get.side_effect = requests.ConnectionError("HPFX and DD both unreachable")

    canada = env_canada.EnvCanada(MagicMock(spec=Session), ModelEnum.GDPS)
    canada.process_model_run_urls(
        ["https://dd.weather.gc.ca/today/model_gdps/15km/00/001/20260623T00Z_MSC_GDPS_AirTemp_AGL-2m_LatLon0.15_PT001H.grib2"],
        fetcher,
    )

    assert canada.connection_error_count == 1
    assert canada.exception_count == 0


def test_http_error_increments_exception_count_not_connection_error_count(monkeypatch):
    """HTTP errors (e.g. 503) from the fetcher are unexpected and must count as exceptions."""
    monkeypatch.setattr(env_canada, "GribFileProcessor", MagicMock)
    monkeypatch.setattr(env_canada, "get_processed_file_record", lambda session, url: None)

    fetcher = MagicMock()
    fetcher.get.side_effect = requests.HTTPError("503 Server Error")

    canada = env_canada.EnvCanada(MagicMock(spec=Session), ModelEnum.GDPS)
    canada.process_model_run_urls(
        ["https://dd.weather.gc.ca/today/model_gdps/15km/00/001/20260623T00Z_MSC_GDPS_AirTemp_AGL-2m_LatLon0.15_PT001H.grib2"],
        fetcher,
    )

    assert canada.exception_count == 1
    assert canada.connection_error_count == 0


def test_process_models_does_not_raise_when_all_urls_already_processed(
    mock_database,
    mock_get_actuals_left_outer_join_with_predictions,
    mock_get_stations_synchronously,
    mock_get_processed_file_count,
    monkeypatch: pytest.MonkeyPatch,
):
    """A clean re-run where all URLs are already in the DB should not fire NoFilesProcessed."""
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    # Return a truthy record for every URL so all are skipped as already processed.
    monkeypatch.setattr(env_canada, "get_processed_file_record", lambda session, url: object())
    sys.argv = ["argv", "GDPS"]
    # Should complete without raising — returns 0 (nothing new to process).
    result = env_canada.process_models()
    assert result == 0


def test_process_models_raises_no_files_processed_when_all_downloads_fail(
    mock_database,
    mock_get_actuals_left_outer_join_with_predictions,
    mock_get_stations_synchronously,
    mock_get_processed_file_count,
    monkeypatch: pytest.MonkeyPatch,
):
    """process_models() raises NoFilesProcessed when every download fails with a connection error."""
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    monkeypatch.setattr(
        env_canada, "get_processed_file_record", lambda session, url: None
    )
    monkeypatch.setattr(requests.Session, "get", MagicMock(side_effect=requests.ConnectionError()))
    sys.argv = ["argv", "GDPS"]
    with pytest.raises(NoFilesProcessed):
        env_canada.process_models()


# How a finished run is judged, over every combination of the three counters it is judged on.
#
# NoFilesProcessed            -> warning to chatops, exits EX_OK (an upstream outage).
# CompletedWithSomeExceptions -> exits EX_SOFTWARE (something we can act on).
# None                        -> no raise, exits EX_OK (success, or nothing new to do).
#
# The rule the corner cases turn on: a real exception always beats an outage, because
# NoFilesProcessed is excused as "the retries will get it" and a genuine bug must not be.
EXIT_DECISION_CASES = [
    # files_processed, connection_errors, exceptions, expected
    (10, 0, 0, None),  # clean run
    (0, 0, 0, None),  # nothing new to do: everything already processed, or not published yet
    (10, 5, 0, None),  # partial outage, but we still got files: retries pick up the rest
    (0, 5, 0, NoFilesProcessed),  # total outage, nothing else wrong
    (0, 5, 3, CompletedWithSomeExceptions),  # outage AND a real bug: the bug wins
    (0, 0, 3, CompletedWithSomeExceptions),  # nothing processed, purely our own fault
    (10, 0, 3, CompletedWithSomeExceptions),  # partial success with real exceptions
    (10, 5, 3, CompletedWithSomeExceptions),  # everything at once: still a real failure
]


# What main() does about each verdict process_models() can reach.
#
# raised_by_process_models, exit_code, chatops_severity (None = no notification at all)
MAIN_OUTCOME_CASES = [
    # A clean run: succeed quietly.
    (None, os.EX_OK, None),
    # An outage on HPFX and DD: tell us, but don't fail the job - hourly retries recover it.
    (NoFilesProcessed("no files processed"), os.EX_OK, "warning"),
    # Real exceptions on some URLs: fail the job. Deliberately no chatops (pre-existing).
    (CompletedWithSomeExceptions(), os.EX_SOFTWARE, None),
    # Anything we didn't see coming: fail loudly.
    (ValueError("boom"), os.EX_SOFTWARE, "critical"),
]


@pytest.mark.parametrize("raised,exit_code,severity", MAIN_OUTCOME_CASES)
def test_main_outcomes(raised, exit_code, severity, mocker, monkeypatch: pytest.MonkeyPatch):
    """Pin the exit code and chatops severity main() produces for every verdict."""
    monkeypatch.setattr(sys, "argv", ["argv", "GDPS"])
    monkeypatch.setattr(env_canada, "apply_data_retention_policy", MagicMock())

    def process_models():
        if raised is not None:
            raise raised

    monkeypatch.setattr(env_canada, "process_models", process_models)
    chatops_spy = mocker.patch.object(env_canada, "send_chatops_notification")

    with pytest.raises(SystemExit) as excinfo:
        env_canada.main()

    assert excinfo.value.code == exit_code

    if severity is None:
        chatops_spy.assert_not_called()
    else:
        chatops_spy.assert_called_once()
        # severity is only passed explicitly for the outage path; otherwise it defaults.
        assert chatops_spy.call_args.kwargs.get("severity", "critical") == severity
        assert "GDPS" in chatops_spy.call_args.args[0]


@pytest.mark.parametrize(
    "files_processed,connection_errors,exceptions,expected", EXIT_DECISION_CASES
)
def test_process_models_exit_decision(
    files_processed,
    connection_errors,
    exceptions,
    expected,
    monkeypatch: pytest.MonkeyPatch,
):
    """Pin how process_models() judges a finished run, for every counter combination."""
    monkeypatch.setattr("wps_shared.db.database.get_write_session_scope", MagicMock())
    monkeypatch.setattr(env_canada, "ModelValueProcessor", MagicMock())
    monkeypatch.setattr(env_canada, "GribFileProcessor", MagicMock())

    def finished_run(self):
        self.files_processed = files_processed
        self.connection_error_count = connection_errors
        self.exception_count = exceptions

    monkeypatch.setattr(env_canada.EnvCanada, "process", finished_run)
    monkeypatch.setattr(sys, "argv", ["argv", "GDPS"])

    if expected is None:
        assert env_canada.process_models() == files_processed
    else:
        with pytest.raises(expected):
            env_canada.process_models()
