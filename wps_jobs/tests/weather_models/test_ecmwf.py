from datetime import datetime
import os
import sys
import pytest
from aiohttp import ClientSession
from pytest_mock import MockerFixture
from unittest.mock import MagicMock
from wps_shared.tests.common import default_mock_client_get
import wps_jobs.weather_model_jobs.ecmwf
from wps_jobs.weather_model_jobs import ModelEnum, ProjectionEnum
from wps_shared.schemas.stations import WeatherStation
from wps_shared.db.crud.model_run_repository import ModelRunRepository
from wps_shared.db.models.weather_models import PredictionModelRunTimestamp

from wps_jobs.weather_model_jobs.ecmwf import (
    get_model_run_hours,
    get_ecmwf_forecast_hours,
    get_stations_dataframe,
    ECMWF,
)
from wps_jobs.weather_model_jobs.ecmwf_model_processor import TEMP, ECMWFModelProcessor
from wps_jobs.weather_model_jobs.utils.process_grib import PredictionModelNotFound


class MockModelRunRepository(ModelRunRepository):
    def __init__(self):
        self.get_or_create_prediction_run_calls = 0
        self.prediction_runs = {}
        self.session = MagicMock()

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


@pytest.fixture
def mock_herbie_instance(mocker: MockerFixture):
    """Fixture to set up a mocked Herbie instance."""
    mock_herbie = MagicMock()
    mocker.patch("wps_jobs.weather_model_jobs.ecmwf.Herbie", mock_herbie)
    mock_herbie_instance = MagicMock()
    mock_herbie.return_value = mock_herbie_instance
    mock_herbie_instance.download.return_value = "/path/to/mock/file.grib"
    mock_herbie_instance.grib = "/path/to/mock/file.grib"
    yield mock_herbie_instance



def test_get_model_run_hours():
    hours = list(get_model_run_hours(ModelEnum.ECMWF))
    assert hours == [0, 12]


def test_get_ecmwf_forecast_hours():
    hours = list(get_ecmwf_forecast_hours())
    assert hours[:5] == [0, 3, 6, 9, 12]
    assert hours[-5:] == [216, 222, 228, 234, 240]


def test_get_stations_dataframe():
    transformer = MagicMock()
    transformer.transform.side_effect = lambda x, y: (x + 1, y + 1)
    stations = [
        WeatherStation(code="001", name="Station1", lat=10.0, long=20.0),
        WeatherStation(code="002", name="Station2", lat=15.0, long=25.0),
    ]
    df = get_stations_dataframe(transformer, stations)
    assert len(df) == 2
    assert df.iloc[0]["latitude"] == 11.0
    assert df.iloc[0]["longitude"] == 21.0

def test_ecmwf_process_model_run_no_url(mock_herbie_instance):
    mock_herbie_instance.grib = None
    stations = [WeatherStation(code="001", name="Station1", lat=10.0, long=20.0)]
    ecmwf = ECMWF("/tmp", stations, MockModelRunRepository())
    ecmwf.process_model_run(0)

    assert ecmwf.files_downloaded == 0
    assert ecmwf.files_processed == 0

@pytest.mark.parametrize(
    "complete, expected_processed, expected_complete_check, expected_complete",
    [
        (False, 65, 1, 1),
        (True, 0, 0, 0)
    ],
)
def test_ecmwf_process_model_complete(complete, expected_processed, expected_complete_check, expected_complete, mock_herbie_instance, mocker: MockerFixture):
    mocker.patch(
        "wps_jobs.weather_model_jobs.ecmwf.get_ecmwf_transformer",
        return_value=MagicMock()
    )
    mocker.patch(
        "wps_jobs.weather_model_jobs.ecmwf.get_stations_dataframe",
        return_value=MagicMock()
    )
    mocker.patch.object(
        ECMWFModelProcessor,
        "process_grib_data",
        return_value=MagicMock()
    )
    # Mock ECMWF.store_processed_result to do nothing
    mocker.patch.object(
        ECMWF,
        "store_processed_result",
        return_value=None
    )
    stations = [WeatherStation(code="001", name="Station1", lat=10.0, long=20.0)]
    mock_repository = MagicMock(spec=ModelRunRepository)
    mock_repository.get_or_create_prediction_run = MagicMock(return_value=MagicMock(complete=complete))
    mock_repository.check_if_model_run_complete = MagicMock(return_value=True)
    ecmwf = ECMWF("/tmp", stations, mock_repository)
    ecmwf.process_model_run(0)

    # For a single hour (0) get all the forecast hours (len(range(0, 145, 3)) + len(range(150, 241, 6))
    assert ecmwf.files_downloaded == expected_processed
    assert ecmwf.files_processed == expected_processed
    assert mock_repository.mark_url_as_processed.call_count == expected_processed
    assert mock_repository.check_if_model_run_complete.call_count == expected_complete_check
    assert mock_repository.mark_prediction_model_run_processed.call_count == expected_complete



def test_ecmwf_process(mock_herbie_instance):
    mock_repo = MockModelRunRepository()
    stations = [WeatherStation(code="001", name="Station1", lat=10.0, long=20.0)]
    ecmwf = ECMWF("/tmp", stations, mock_repo)
    ecmwf.process()

    assert mock_repo.get_or_create_prediction_run_calls == 2  # For hours 0 and 12
    # For each hour (0 and 12) get all the forecast hours (2 * (len(range(0, 145, 3)) + len(range(150, 241, 6)))
    assert ecmwf.files_downloaded == 130
    assert ecmwf.files_processed == 130


def test_ecmwf_process_model_run_prediction_not_found(mock_herbie_instance, monkeypatch):
    def mock_get_transformer(_, __):
        raise Exception()

    monkeypatch.setattr(wps_jobs.weather_model_jobs.ecmwf, "get_ecmwf_transformer", mock_get_transformer)

    stations = [WeatherStation(code="001", name="Station1", lat=10.0, long=20.0)]
    ecmwf = ECMWF("/tmp", stations, MockModelRunRepository())

    ecmwf.process()
    # For each hour (0 and 12) get all the forecast hours (2 * (len(range(0, 145, 3)) + len(range(150, 241, 6)))
    assert ecmwf.exception_count == 130

@pytest.mark.parametrize(
    "prediction_exists",
    [
        (True),
        (False)
    ],
)
def test_store_processed_result(prediction_exists):
    mock_repo = MagicMock(spec=ModelRunRepository)
    if not prediction_exists:
        mock_repo.get_model_run_prediction.return_value = None

    mock_prediction_run = MagicMock(spec=PredictionModelRunTimestamp)
    mock_prediction_run.id = 1

    mock_process_result = MagicMock()
    mock_process_result.model_run_info.prediction_timestamp = "2025-05-01T12:00:00Z"
    mock_process_result.data.sel.return_value = {
        "temperature": MagicMock(item=lambda: 25.0),
        "humidity": MagicMock(item=lambda: 60.0),
    }

    stations = [
        WeatherStation(code="001", name="Station1", lat=10.0, long=20.0),
        WeatherStation(code="002", name="Station2", lat=15.0, long=25.0),
    ]

    ecmwf = ECMWF("/tmp", stations, mock_repo)

    ecmwf.store_processed_result(stations, mock_prediction_run, mock_process_result)

    assert mock_repo.get_model_run_prediction.call_count == len(stations)
    assert mock_repo.store_model_run_prediction.call_count == len(stations)


def test_ecmwf_process_handles_exceptions(monkeypatch):
    mock_repo = MagicMock(spec=ModelRunRepository)
    stations = [WeatherStation(code="001", name="Station1", lat=10.0, long=20.0)]
    monkeypatch.setattr(wps_jobs.weather_model_jobs.ecmwf.ECMWF, "process_model_run", lambda: Exception("Mocked exception"))


    ecmwf = ECMWF("/tmp", stations, mock_repo)
    ecmwf.process()

    assert ecmwf.exception_count > 0

def test_main_success(mocker: MockerFixture, monkeypatch):
    """Test the main function when it runs successfully."""
    async def mock_process_models():
        pass
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    monkeypatch.setattr(wps_jobs.weather_model_jobs.ecmwf, "process_models", mock_process_models)
    rocket_chat_spy = mocker.spy(wps_jobs.weather_model_jobs.ecmwf, "send_rocketchat_notification")

    with pytest.raises(SystemExit) as excinfo:
        wps_jobs.weather_model_jobs.ecmwf.main()
    
     # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_OK
    # Assert that rocket chat was called.
    assert rocket_chat_spy.call_count == 0


def test_main_fail(mocker: MockerFixture, monkeypatch):
    """ Run the main method, check that message is sent to rocket chat, and exit code is EX_SOFTWARE """
    def mock_process_models():
        raise Exception()

    rocket_chat_spy = mocker.spy(wps_jobs.weather_model_jobs.ecmwf, "send_rocketchat_notification")
    monkeypatch.setattr(wps_jobs.weather_model_jobs.ecmwf, "process_models", mock_process_models)

    with pytest.raises(SystemExit) as excinfo:
        wps_jobs.weather_model_jobs.ecmwf.main()

    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_SOFTWARE
    # Assert that rocket chat was called.
    assert rocket_chat_spy.call_count == 1

@pytest.mark.anyio
async def test_process_models_success(mocker: MockerFixture):
    """Test process_models when it runs successfully."""
    mock_stations = [
        WeatherStation(code="001", name="Station1", lat=10.0, long=20.0),
        WeatherStation(code="002", name="Station2", lat=15.0, long=25.0),
    ]
    mock_repo = MockModelRunRepository()
    mock_session_scope = MagicMock()
    mock_session_scope.return_value.__enter__.return_value = mock_repo
    mock_temp_dir = MagicMock()
    mock_temp_dir.return_value.__enter__.return_value = "/mock/temp/dir"
    mocker.patch("tempfile.TemporaryDirectory", mock_temp_dir)
    mocker.patch("wps_jobs.weather_model_jobs.ecmwf.get_stations_asynchronously", return_value=mock_stations)
    mocker.patch("wps_jobs.weather_model_jobs.ecmwf.get_write_session_scope", return_value=mock_session_scope)

    mock_ecmwf = mocker.patch("wps_jobs.weather_model_jobs.ecmwf.ECMWF")
    mock_ecmwf_instance = mock_ecmwf.return_value
    mock_ecmwf_instance.files_processed = 10


    mock_temp_dir.return_value.__enter__.return_value = "/mock/temp/dir"
    mock_session_scope.return_value.__enter__.return_value = mock_repo

    await wps_jobs.weather_model_jobs.ecmwf.process_models()

    mock_ecmwf_instance.process.assert_called_once()

def test_process_model_run_prediction_model_not_found():
    """Test process_model_run when prediction model is not found."""
    stations = [WeatherStation(code="001", name="Station1", lat=10.0, long=20.0)]
    mock_repo = MockModelRunRepository()
    mock_repo.get_prediction_model = MagicMock(return_value=None)  # Simulate missing prediction model
    ecmwf = ECMWF("/tmp", stations, mock_repo)

    with pytest.raises(PredictionModelNotFound):
        ecmwf.process_model_run(0)

    assert ecmwf.files_downloaded == 0
    assert ecmwf.files_processed == 0
    assert ecmwf.exception_count == 0

@pytest.mark.parametrize(
    "complete",
    [
        (True),
        (False)
    ],
)
def test_process_model_run_prediction_model_complete(complete):
    """Test process_model_run when prediction model is not found."""
    stations = [WeatherStation(code="001", name="Station1", lat=10.0, long=20.0)]
    mock_repo = MockModelRunRepository()
    mock_prediction_run = MagicMock(spec=PredictionModelRunTimestamp)
    if complete:
        mock_prediction_run.complete = True
    mock_repo.get_or_create_prediction_run = mock_prediction_run
    ecmwf = ECMWF("/tmp", stations, mock_repo)

    ecmwf.process_model_run(0)

    assert ecmwf.files_downloaded == 0
    assert ecmwf.files_processed == 0
    assert ecmwf.exception_count == 0

def test_get_model_run_urls(mock_herbie_instance):
    """Test get_model_run_urls to ensure it returns the correct URLs."""
    mock_herbie_instance.grib = "/mock/path/to/file.grib"

    urls = wps_jobs.weather_model_jobs.ecmwf.get_model_run_urls(datetime(2023, 1, 1, 0, 0))

    # Ensure the number of URLs matches the forecast hours
    expected_forecast_hours = len(list(get_ecmwf_forecast_hours()))
    assert len(urls) == expected_forecast_hours

    # Ensure all URLs are the mocked grib file path
    assert all(url == "/mock/path/to/file.grib" for url in urls)


def test_get_model_run_urls_no_grib(mock_herbie_instance):
    """Test get_model_run_urls when no grib files are found."""
    mock_herbie_instance.grib = None  # Simulate no grib file found

    urls = wps_jobs.weather_model_jobs.ecmwf.get_model_run_urls(datetime(2023, 1, 1, 0, 0))

    # Ensure no URLs are returned
    assert len(urls) == 0
