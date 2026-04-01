from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from wps_shared.db.models.psu import FireCentre


@pytest.fixture()
def client():
    from app.main import app as test_app

    with TestClient(test_app) as test_client:
        yield test_client


@pytest.mark.usefixtures("mock_jwt_decode")
@patch("app.routers.psu.fetch_fire_centres")
def test_psu_fire_centres_endpoint(mock_fetch_fire_centres, client: TestClient):
    mock_fetch_fire_centres.return_value = [
        FireCentre(id=1, name="Coastal Fire Centre"),
        FireCentre(id=2, name="Northwest Fire Centre"),
    ]

    response = client.get("/api/psu/fire-centres")

    assert response.status_code == 200
    assert response.json() == {
        "fire_centres": [
            {"id": 1, "name": "Coastal Fire Centre"},
            {"id": 2, "name": "Northwest Fire Centre"},
        ]
    }
