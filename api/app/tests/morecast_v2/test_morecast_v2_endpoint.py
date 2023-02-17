from fastapi.testclient import TestClient
import pytest
from app.schemas.morecast_v2 import (ForecastedPrecip, ForecastedRH,
                                     ForecastedTemperature,
                                     ForecastedWindDirection,
                                     ForecastedWindSpeed,
                                     ModelChoice,
                                     MorecastForecastRequest)
import app.routers.morecast_v2
from app.tests.utils.mock_jwt_decode_role import MockJWTDecodeWithRole


morecast_v2_post_url = '/api/morecast-v2/forecast'
morecast_v2_get_url = f'/api/morecast-v2/forecasts/{1}'

decode_fn = "jwt.decode"

forecast = MorecastForecastRequest(station_code=1,
                                   for_date=1,
                                   temp=ForecastedTemperature(
                                       temp=10.0, choice=ModelChoice.GDPS),
                                   rh=ForecastedRH(rh=40.5, choice=ModelChoice.HRDPS),
                                   precip=ForecastedPrecip(
                                       precip=70.2, choice=ModelChoice.MANUAL),
                                   wind_speed=ForecastedWindSpeed(
                                       wind_speed=20.3, choice=ModelChoice.RDPS),
                                   wind_direction=ForecastedWindDirection(wind_direction=40,
                                                                          choice=ModelChoice.GDPS))


@pytest.fixture()
def client():
    from app.main import app as test_app

    with TestClient(test_app) as test_client:
        yield test_client


def test_get_forecast_unauthorized(client: TestClient):
    """ forecast role required for retriecing forecasts """
    response = client.get(morecast_v2_get_url)
    assert response.status_code == 401


def test_get_forecast_authorized(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """ forecast role required for persisting a forecast """

    def mock_admin_role_function(*_, **__):
        return MockJWTDecodeWithRole('forecaster')

    monkeypatch.setattr(decode_fn, mock_admin_role_function)
    monkeypatch.setattr(app.routers.morecast_v2, 'get_user_forecasts_for_date', lambda *_: [])

    response = client.get(morecast_v2_get_url)
    assert response.status_code == 200


def test_post_forecast_unauthorized(client: TestClient):
    """ forecast role required for persisting a forecast """
    response = client.post(morecast_v2_post_url, json=[])
    assert response.status_code == 401


def test_post_forecast_authorized(client: TestClient,
                                  monkeypatch: pytest.MonkeyPatch):
    """ Allowed to post station changes with correct role"""

    def mock_admin_role_function(*_, **__):
        return MockJWTDecodeWithRole('forecaster')

    monkeypatch.setattr(decode_fn, mock_admin_role_function)

    response = client.post(morecast_v2_post_url, json=[forecast.dict()])
    assert response.status_code == 201


def test_post_forecast_authorized_with_body(client: TestClient,
                                            monkeypatch: pytest.MonkeyPatch):
    """ Allowed to post station changes with correct role"""

    def mock_admin_role_function(*_, **__):
        return MockJWTDecodeWithRole('forecaster')

    monkeypatch.setattr(decode_fn, mock_admin_role_function)

    response = client.post(morecast_v2_post_url, json=[forecast.dict()])
    assert response.status_code == 201
