from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
import pytest

from app.tests.utils.mock_jwt_decode_role import MockJWTDecodeWithRole
import app.routers.hfi_calc


add_stations_json = {
    "fire_centre_id": 1,
    "added": [
        {
            "planning_area_id": 1,
            "station_code": 101,
            "fuel_type_id": 1,
        },
        {
            "planning_area_id": 1,
            "station_code": 102,
            "fuel_type_id": 2,
        },
        {
            "planning_area_id": 2,
            "station_code": 103,
            "fuel_type_id": 3,
        }
    ],
    "removed": []
}

post_admin_stations_url = '/api/hfi-calc/admin/stations'
decode_fn = "jwt.decode"


@pytest.fixture()
def client():
    from app.main import app as test_app

    with TestClient(test_app) as test_client:
        yield test_client


def test_post_stations_unauthorized(client: TestClient):
    """ hfi_station_admin role required for updating stations"""
    response = client.post(post_admin_stations_url, json=add_stations_json)
    assert response.status_code == 401


def test_post_stations_authorized(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """ Allowed to post station changes with correct role"""

    def mock_admin_role_function(*_, **__):  # pylint: disable=unused-argument
        return MockJWTDecodeWithRole('hfi_station_admin')

    monkeypatch.setattr(decode_fn, mock_admin_role_function)

    response = client.post(post_admin_stations_url, json=add_stations_json)
    assert response.status_code == 200


def test_post_stations_authorized_with_date_range(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """ Update stations with date range"""

    def mock_admin_role_function(*_, **__):  # pylint: disable=unused-argument
        return MockJWTDecodeWithRole('hfi_station_admin')

    monkeypatch.setattr(decode_fn, mock_admin_role_function)

    update_stations_json = {
        "fire_centre_id": 1,
        "added": [
            {
                "planning_area_id": 1,
                "station_code": 101,
                "fuel_type_id": 1,
            }
        ],
        "removed": [],
        "date_range": {"start_date": "2020-05-21", "end_date": "2020-05-26"}
    }
    response = client.post(post_admin_stations_url, json=update_stations_json)
    assert response.status_code == 200


def test_post_stations_wrong_role(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """ Should not be allowed to post station changes with incorrect role"""

    def mock_admin_role_function(*_, **__):  # pylint: disable=unused-argument
        return MockJWTDecodeWithRole('hfi_set_ready_state')

    monkeypatch.setattr(decode_fn, mock_admin_role_function)

    response = client.post(post_admin_stations_url, json=add_stations_json)
    assert response.status_code == 401


def test_post_stations_duplicate_station(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """ Duplicate error should return a 400 """

    def mock_admin_role_function(*_, **__):  # pylint: disable=unused-argument
        return MockJWTDecodeWithRole('hfi_station_admin')

    def mock_db_integrity_error(*_, **__):  # pylint: disable=unused-argument
        raise IntegrityError(MagicMock(), MagicMock(), MagicMock())

    monkeypatch.setattr(decode_fn, mock_admin_role_function)
    monkeypatch.setattr(app.routers.hfi_calc, 'save_hfi_stations', mock_db_integrity_error)

    response = client.post(post_admin_stations_url, json=add_stations_json)
    assert response.status_code == 400
