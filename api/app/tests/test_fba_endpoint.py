import json

import pytest
from aiohttp import ClientSession
from starlette.testclient import TestClient

import app.main
from app.tests import get_complete_filename
from app.tests.common import default_mock_client_get


@pytest.mark.usefixtures("mock_jwt_decode")
@pytest.mark.parametrize("status, expected_fire_centers", [(200, "test_fba_endpoint_fire_centers.json")])
def test_fba_endpoint_fire_centers(status, expected_fire_centers, monkeypatch):
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)

    client = TestClient(app.main.app)
    headers = {"Content-Type": "application/json", "Authorization": "Bearer token"}

    response = client.get("/api/fba/fire-centers/", headers=headers)

    response_filename = get_complete_filename(__file__, expected_fire_centers)
    with open(response_filename) as res_file:
        expected_response = json.load(res_file)

    assert response.status_code == status
    assert response.json() == expected_response
