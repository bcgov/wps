from datetime import date
from unittest.mock import patch

import app.main
import pytest
from fastapi.testclient import TestClient
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum
from wps_shared.schemas.sfms import SFMSRunBounds

client = TestClient(app.main.app)

get_sfmsng_run_bounds_url = "/api/sfmsng/run-bounds"


async def mock_get_sfms_insights_bounds(*_, **__):
    return [
        SFMSRunBounds(
            year=2025,
            run_type=RunTypeEnum.actual,
            minimum=date(2025, 4, 5),
            maximum=date(2025, 9, 25),
        ),
    ]


async def mock_get_sfms_insights_bounds_no_data(*_, **__):
    return []


@pytest.mark.usefixtures("mock_jwt_decode")
@patch("app.routers.sfmsng.get_sfms_insights_bounds", mock_get_sfms_insights_bounds)
def test_get_sfmsng_run_bounds():
    response = client.get(get_sfmsng_run_bounds_url)
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["sfms_bounds"]["2025"]["actual"]["minimum"] == "2025-04-05"
    assert json_response["sfms_bounds"]["2025"]["actual"]["maximum"] == "2025-09-25"


@pytest.mark.usefixtures("mock_jwt_decode")
@patch(
    "app.routers.sfmsng.get_sfms_insights_bounds",
    mock_get_sfms_insights_bounds_no_data,
)
def test_get_sfmsng_run_bounds_no_bounds():
    response = client.get(get_sfmsng_run_bounds_url)
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["sfms_bounds"] == {}
