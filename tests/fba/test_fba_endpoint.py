from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from tests.utils.mock_jwt_decode_role import MockJWTDecodeWithRole

get_fire_centres_url = '/api/fba/fire-centers'
get_fire_zone_areas_url = '/api/fba/fire-zone-areas/forecast/2022-09-27/2022-09-27'
decode_fn = "jwt.decode"


async def mock_get_fire_centres(*_, **__):  # pylint: disable=unused-argument
    return []


async def mock_get_hfi_area(*_, **__):  # pylint: disable=unused-argument
    return []


async def mock_get_auth_header(*_, **__):  # pylint: disable=unused-argument
    return {}


def mock_admin_role_function(*_, **__):  # pylint: disable=unused-argument
    return MockJWTDecodeWithRole('hfi_station_admin')


@pytest.fixture()
def client():
    from app.main import app as test_app

    with TestClient(test_app) as test_client:
        yield test_client


@patch('app.routers.fba.get_auth_header', mock_get_auth_header)
@patch('app.routers.fba.get_fire_centers', mock_get_fire_centres)
@patch(decode_fn, mock_admin_role_function)
def test_get_fire_centres_authorized(client: TestClient):
    """ Allowed to get fire centres when authorized"""
    response = client.get(get_fire_centres_url)
    assert response.status_code == 200


def test_get_fire_centres_unauthorized(client: TestClient):
    """ Forbidden to get fire centres when unauthorized"""

    response = client.get(get_fire_centres_url)
    assert response.status_code == 401


def test_get_fire_zone_areas_unauthorized(client: TestClient):
    """ Forbidden to get fire zone areas when unauthorized"""

    response = client.get(get_fire_zone_areas_url)
    assert response.status_code == 401


@patch('app.routers.fba.get_hfi_area', mock_get_hfi_area)
@patch(decode_fn, mock_admin_role_function)
def test_get_fire_zone_areas_unauthorized(client: TestClient):
    """ Forbidden to get fire zone areas when unauthorized"""

    response = client.get(get_fire_zone_areas_url)
    assert response.status_code == 200
