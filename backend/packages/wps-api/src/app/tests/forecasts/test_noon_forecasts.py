import json
import os
from datetime import datetime

import app.main
import pytest
from aiohttp import ClientSession
from sqlalchemy.orm import Session
from starlette.testclient import TestClient
from wps_shared.db.models.forecasts import NoonForecast
from wps_shared.tests.common import default_mock_client_get
from wps_wf1.models import StationCodeList


def mock_query_noon_forecast_records(
    session: Session, station_codes: StationCodeList, start_date: datetime, end_date: datetime
):
    """Mock some noon forecasts"""
    forecasts = []
    dirname = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(dirname, "test_noon_forecasts.json")
    with open(filename) as data:
        json_data = json.load(data)
        for forecast in json_data:
            forecast["weather_date"] = datetime.fromisoformat(forecast["weather_date"])
            forecast["created_at"] = datetime.fromisoformat(forecast["created_at"])
            forecasts.append(NoonForecast(**forecast))
    return forecasts


@pytest.mark.parametrize(
    "codes,status,num_groups",
    [([209], 200, 1)],
)
@pytest.mark.usefixtures("mock_jwt_decode")
def test_noon_forecasts(codes, status, num_groups, monkeypatch):
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    monkeypatch.setattr(
        app.forecasts.noon_forecasts,
        "query_noon_forecast_records",
        mock_query_noon_forecast_records,
    )

    client = TestClient(app.main.app)
    headers = {"Content-Type": "application/json", "Authorization": "Bearer token"}
    response = client.post("/api/forecasts/noon/", headers=headers, json={"stations": codes})
    assert response.status_code == status
    assert len(response.json()["noon_forecasts"]) == num_groups
