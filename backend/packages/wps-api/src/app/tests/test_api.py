""" Unit tests for API.
"""
import pytest
from aiohttp import ClientSession
from starlette.testclient import TestClient
import app.main
from wps_shared.tests.common import default_mock_client_get


PERCENTILE_URL = '/api/percentiles/'


""" Some basic unit tests. """


def test_stations(monkeypatch: pytest.MonkeyPatch):
    """Test that stations request returns 200/OK."""
    client = TestClient(app.main.app)
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    response = client.get("/api/stations")
    assert response.status_code == 200


def test_percentile(monkeypatch: pytest.MonkeyPatch):
    """Test that a request for percentiles return 200/OK."""
    client = TestClient(app.main.app)
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    response = client.post(PERCENTILE_URL, headers={"Content-Type": "application/json"}, json={"stations": ["331", "328"], "percentile": 90, "year_range": {"start": 2014, "end": 2023}})
    assert response.status_code == 200


def test_percentile_no_stations_errors(monkeypatch: pytest.MonkeyPatch):
    """Test to check for empty stations array. If no stations are provided in the request,
    the expected behavious is to get back a 400 error."""
    client = TestClient(app.main.app)
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    response = client.post(PERCENTILE_URL, headers={"Content-Type": "application/json"}, json={"stations": [], "percentile": 90, "year_range": {"start": 2010, "end": 2019}})
    assert response.status_code == 400


def test_percentile_no_invalid_year_errors(monkeypatch: pytest.MonkeyPatch):
    """Test to check for invalid year range. If an invalid year range is specified, the requested
    behaviour is to get back a 400 error."""
    client = TestClient(app.main.app)
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    response = client.post(PERCENTILE_URL, headers={"Content-Type": "application/json"}, json={"stations": ["331", "328"], "percentile": 90, "year_range": {"start": 2004, "end": 2019}})
    assert response.status_code == 400
