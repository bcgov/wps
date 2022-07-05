from fastapi.testclient import TestClient
import pytest


add_stations_json = {
    "added": [
        {
            "planning_area_id": 1,
            "station_code": 101,
            "fuel_type_id": 1,
            "row_id": 0
        },
        {
            "planning_area_id": 1,
            "station_code": 102,
            "fuel_type_id": 2,
            "row_id": 1
        },
        {
            "planning_area_id": 2,
            "station_code": 103,
            "fuel_type_id": 3,
            "row_id": 0
        }
    ],
    "removed": []
}


class MockJWTDecodeWithRole:
    """ Mock pyjwt module with role """

    def __init__(self, role):
        self.decoded_token = {
            "preferred_username": "test_username",
            "resource_access": {
                "wps-web": {
                    "roles": [
                        role
                    ]
                }
            }}

    def __getitem__(self, key):
        return self.decoded_token[key]

    def get(self, key, _):
        "Returns the mock decoded token"
        return self.decoded_token[key]

    def decode(self):
        "Returns the mock decoded token"
        return self.decoded_token


post_admin_stations_url = '/api/hfi-calc/admin/stations'


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

    monkeypatch.setattr("jwt.decode", mock_admin_role_function)

    response = client.post(post_admin_stations_url, json=add_stations_json)
    assert response.status_code == 200


def test_post_stations_wrong_role(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """ Allowed to post station changes with incorrect role"""

    def mock_admin_role_function(*_, **__):  # pylint: disable=unused-argument
        return MockJWTDecodeWithRole('hfi_set_ready_state')

    monkeypatch.setattr("jwt.decode", mock_admin_role_function)

    response = client.post(post_admin_stations_url, json=add_stations_json)
    assert response.status_code == 401
