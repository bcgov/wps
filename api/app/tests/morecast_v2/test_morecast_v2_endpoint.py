import aiohttp
from fastapi.testclient import TestClient
from httpx import AsyncClient
import pytest
from datetime import datetime
from aiohttp import ClientSession
from wps_shared.schemas.shared import StationsRequest
from wps_shared.tests.common import default_mock_client_get
from wps_shared.schemas.morecast_v2 import MoreCastForecastInput, MoreCastForecastRequest, StationDailyFromWF1
import app.routers.morecast_v2
from app.tests.utils.mock_jwt_decode_role import MockJWTDecodeWithRole


morecast_v2_post_url = "/api/morecast-v2/forecast"
morecast_v2_get_url = "/api/morecast-v2/forecasts/2023-03-15"
morecast_v2_post_by_date_range_url = "/api/morecast-v2/forecasts/2023-03-15/2023-03-19"
today = "2022-10-07"
morecast_v2_post_yesterday_dailies_url = f"/api/morecast-v2/yesterday-dailies/{today}"
morecast_v2_post_determinates_url = "/api/morecast-v2/determinates/2023-03-15/2023-03-19"


decode_fn = "jwt.decode"

forecast = MoreCastForecastRequest(token="testToken", forecasts=[MoreCastForecastInput(station_code=1, for_date=1, temp=10.0, rh=40.1, precip=70.2, wind_speed=20.3, wind_direction=40)])

stations = StationsRequest(stations=[1, 2])


@pytest.fixture()
def client():
    from app.main import app as test_app

    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture()
async def async_client():
    from app.main import app as test_app

    async with AsyncClient(app=test_app, base_url="https://test") as test_client:
        yield test_client


def test_get_forecast_unauthorized(client: TestClient):
    """forecast role required for retrieving forecasts"""
    response = client.get(morecast_v2_get_url)
    assert response.status_code == 401


def test_get_forecast_authorized(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """forecast role required for persisting a forecast"""

    def mock_admin_role_function(*_, **__):
        return MockJWTDecodeWithRole("morecast2_write_forecast")

    monkeypatch.setattr(decode_fn, mock_admin_role_function)
    monkeypatch.setattr(app.routers.morecast_v2, "get_user_forecasts_for_date", lambda *_: [])

    response = client.get(morecast_v2_get_url)
    assert response.status_code == 200


def test_post_forecast_unauthorized(client: TestClient):
    """forecast role required for persisting a forecast"""
    response = client.post(morecast_v2_post_url, json=[])
    assert response.status_code == 401


@pytest.mark.anyio
def test_post_forecast_authorized(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """Allowed to post station changes with correct role"""

    def mock_admin_role_function(*_, **__):
        return MockJWTDecodeWithRole("morecast2_write_forecast")

    monkeypatch.setattr(decode_fn, mock_admin_role_function)

    async def mock_format_as_wf1_post_forecasts(client_session, forecasts_to_save, username, headers):
        return []

    monkeypatch.setattr(app.routers.morecast_v2, "format_as_wf1_post_forecasts", mock_format_as_wf1_post_forecasts)

    async def mock_post_forecasts(client_session, forecasts):
        return None

    monkeypatch.setattr(app.routers.morecast_v2, "post_forecasts", mock_post_forecasts)

    async def mock_get_auth_header(_):
        return dict()

    monkeypatch.setattr(app.routers.morecast_v2, "get_auth_header", mock_get_auth_header)

    response = client.post(morecast_v2_post_url, json=forecast.model_dump())
    assert response.status_code == 201


@pytest.mark.anyio
def test_post_forecast_authorized_error(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """Allowed to post station changes with correct role"""

    def mock_admin_role_function(*_, **__):
        return MockJWTDecodeWithRole("morecast2_write_forecast")

    monkeypatch.setattr(decode_fn, mock_admin_role_function)

    async def mock_format_as_wf1_post_forecasts(client_session, forecasts_to_save, username, headers):
        return []

    monkeypatch.setattr(app.routers.morecast_v2, "format_as_wf1_post_forecasts", mock_format_as_wf1_post_forecasts)

    class MockResponse:
        status = 500

        async def text(self):
            return "Bad Request"

    class MockClientSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def post(self, url):
            return MockResponse()

    # Use monkeypatch to replace the ClientSession with our mock class
    monkeypatch.setattr(aiohttp, "ClientSession", lambda: MockClientSession())

    async def mock_get_auth_header(_):
        return dict()

    monkeypatch.setattr(app.routers.morecast_v2, "get_auth_header", mock_get_auth_header)

    response = client.post(morecast_v2_post_url, json=forecast.model_dump())
    assert response.status_code == 500
    assert (
        response.json()["detail"]
        == """
        Error submitting forecasts to WF1, please retry.
        All your forecast inputs have been saved as a draft on your browser and can be submitted at a later time.
        If the problem persists, use the following link to verify the status of the WF1 service: https://wfapps.nrs.gov.bc.ca/pub/wfwx-fireweather-web/stations
    """
    )


def test_post_forecasts_by_date_range_unauthorized(client: TestClient):
    """forecast role required for persisting a forecast"""
    response = client.post(morecast_v2_post_by_date_range_url, json=[])
    assert response.status_code == 401


def test_post_forecast_by_date_range_authorized(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """Allowed to post station changes with correct role"""

    def mock_admin_role_function(*_, **__):
        return MockJWTDecodeWithRole("morecast2_write_forecast")

    monkeypatch.setattr(decode_fn, mock_admin_role_function)

    response = client.post(morecast_v2_post_by_date_range_url, json=stations.model_dump())
    assert response.status_code == 200


def test_get_yesterday_dailies_unauthorized(client: TestClient):
    """user must be authenticated to retrieve yesterday dailies"""
    response = client.post(morecast_v2_post_yesterday_dailies_url, json={"station_codes": [209, 211, 302]})
    assert response.status_code == 401


def test_get_yesterday_dailies_authorized(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """user must be authenticated to retrieve yesterday dailies"""

    def mock_admin_role_function(*_, **__):
        return MockJWTDecodeWithRole("morecast2_write_forecast")

    monkeypatch.setattr(decode_fn, mock_admin_role_function)
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)

    requested_station_codes = [209, 211, 302]

    response = client.post(morecast_v2_post_yesterday_dailies_url, json={"station_codes": requested_station_codes})
    assert response.status_code == 200

    parsed_dailies = [StationDailyFromWF1.model_validate(raw_daily) for raw_daily in response.json().get("dailies")]
    assert len(parsed_dailies) == 3

    today_date = datetime.strptime(today, "%Y-%m-%d").date()
    for requested_station_code, response in zip(requested_station_codes, parsed_dailies):
        assert requested_station_code == response.station_code
        assert response.utcTimestamp.tzname() == "UTC"
        assert response.utcTimestamp.year == today_date.year
        assert response.utcTimestamp.month == today_date.month
        assert response.utcTimestamp.day == today_date.day - 1
        assert response.utcTimestamp.hour == 20


def test_get_determinates_unauthorized(client: TestClient):
    response = client.post(morecast_v2_post_determinates_url, json={"station_codes": [209, 211, 302]})
    assert response.status_code == 401


@pytest.mark.anyio
async def test_get_determinates_authorized(anyio_backend, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
    def mock_admin_role_function(*_, **__):
        return MockJWTDecodeWithRole("morecast2_write_forecast")

    monkeypatch.setattr(decode_fn, mock_admin_role_function)
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)

    response = await async_client.post(morecast_v2_post_determinates_url, json={"stations": [209, 211, 302]})
    assert response.status_code == 200
