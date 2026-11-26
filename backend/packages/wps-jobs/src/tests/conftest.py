import pytest
from unittest.mock import MagicMock
import wps_shared.db.database
import wps_weather_data.table
from wps_weather_data.weather_data_addresser import WeatherDataAddresser
from wps_shared.tests.conftest import (
    anyio_backend,
    mock_env,
    mock_aiobotocore_get_session,
    mock_requests,
    mock_redis,
    mock_get_now,
    mock_get_pst_today_start_and_end,
    mock_jwt_decode,
    mock_sentry,
    mock_requests_session,
    mock_client_session,
    spy_access_logging,
    mock_wfwx_api,
)


@pytest.fixture(autouse=True)
def mock_session(monkeypatch):
    """Ensure that all unit tests mock out the database session by default!"""
    monkeypatch.setattr(wps_shared.db.database, "_get_write_session", MagicMock())
    monkeypatch.setattr(wps_shared.db.database, "_get_read_session", MagicMock())


@pytest.fixture(autouse=True)
def local_station_weather_tables(monkeypatch, tmp_path):
    """Keep the station weather Delta tables (`staging`, `runs`, `by_time`) in a temporary
    directory instead of the object store, so tests read and write real, empty tables."""
    monkeypatch.setattr(
        WeatherDataAddresser, "delta_uri", lambda self, key: str(tmp_path / "tables" / key)
    )
    monkeypatch.setattr(wps_weather_data.table, "object_store_options", lambda: None)
