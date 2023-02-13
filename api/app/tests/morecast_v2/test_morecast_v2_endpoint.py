from fastapi.testclient import TestClient
import pytest

from app.tests.utils.mock_jwt_decode_role import MockJWTDecodeWithRole


morecast_v2_url = '/api/morecast-v2/forecast'
decode_fn = "jwt.decode"


@pytest.fixture()
def client():
    from app.main import app as test_app

    with TestClient(test_app) as test_client:
        yield test_client


def test_post_forecast_unauthorized(client: TestClient):
    """ forecast role required for persisting a forecast"""
    response = client.post(morecast_v2_url)
    assert response.status_code == 401


def test_post_forecast_authorized(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """ Allowed to post station changes with correct role"""

    def mock_admin_role_function(*_, **__):  # pylint: disable=unused-argument
        return MockJWTDecodeWithRole('forecaster')

    monkeypatch.setattr(decode_fn, mock_admin_role_function)

    response = client.post(morecast_v2_url)
    assert response.status_code == 200
