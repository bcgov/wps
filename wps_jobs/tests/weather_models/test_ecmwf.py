import pytest
from unittest.mock import MagicMock, patch
import wps_jobs.weather_model_jobs.ecmwf
from wps_jobs.weather_model_jobs import ModelEnum
from wps_shared.schemas.stations import WeatherStation
from wps_shared.db.crud.model_run_repository import ModelRunRepository

from wps_jobs.weather_model_jobs.ecmwf import (
    get_model_run_hours,
    get_ecmwf_forecast_hours,
    get_stations_dataframe,
    ECMWF,
)


class MockModelRunRepository(ModelRunRepository):
    def __init__(self):
        self.get_or_create_prediction_run_calls = 0
        self.prediction_runs = {}

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
def mock_herbie_instance():
    """Fixture to set up a mocked Herbie instance."""
    with patch("wps_jobs.weather_model_jobs.ecmwf.Herbie") as mock_herbie:
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


def test_ecmwf_process_model_run(mock_herbie_instance):
    stations = [WeatherStation(code="001", name="Station1", lat=10.0, long=20.0)]
    ecmwf = ECMWF("/tmp", stations, MockModelRunRepository())
    ecmwf.process_model_run(0)

    # For a single hour (0) get all the forecast hours (len(range(0, 145, 3)) + len(range(150, 241, 6))
    assert ecmwf.files_downloaded == 65
    assert ecmwf.files_processed == 65


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
