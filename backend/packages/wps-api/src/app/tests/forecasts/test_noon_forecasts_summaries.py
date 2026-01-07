from datetime import datetime, timedelta

import app.main
import pytest
import wps_shared.utils.time as time_utils
from aiohttp import ClientSession
from sqlalchemy.orm import Session
from starlette.testclient import TestClient
from wps_shared.db.models.forecasts import NoonForecast
from wps_shared.tests.common import default_mock_client_get
from wps_wf1.models import StationCodeList

noon = time_utils.get_utc_now().replace(hour=20, minute=0, second=0, microsecond=0)
weather_date = noon - timedelta(days=2)

# they should have the same length
mock_tmps = [20, 21, 22]
mock_rhs = [50, 51, 52]


def mock_query_noon_forecast_records(
    session: Session, station_codes: StationCodeList, start_date: datetime, end_date: datetime
):
    """Mock some noon forecasts"""
    forecasts = []
    weather_values = []
    for index, tmp in enumerate(mock_tmps):
        weather_values.append({"tmp": tmp, "rh": mock_rhs[index]})

    for code in [209, 322]:
        for value in weather_values:
            forecasts.append(
                NoonForecast(
                    station_code=code,
                    weather_date=weather_date,
                    created_at=time_utils.get_utc_now(),
                    temperature=value["tmp"],
                    relative_humidity=value["rh"],
                )
            )
    return forecasts


@pytest.mark.parametrize(
    "codes,status,num_summaries", [([999], 200, 0), ([322], 200, 1), ([322, 838], 200, 2)]
)
@pytest.mark.usefixtures("mock_jwt_decode")
def test_noon_forecast_summaries(codes, status, num_summaries, monkeypatch):
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    monkeypatch.setattr(
        app.forecasts.noon_forecasts_summaries,
        "query_noon_forecast_records",
        mock_query_noon_forecast_records,
    )
    client = TestClient(app.main.app)
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    response = client.post(
        "/api/forecasts/noon/summaries/",
        headers={"Authorization": "Bearer token"},
        json={"stations": codes},
    )
    assert response.status_code == status
    assert len(response.json()["summaries"]) == num_summaries

    # Check if we calculate correct percentiles based on its noon forecasts
    result = response.json()
    tmp_min = min(mock_tmps)
    tmp_max = max(mock_tmps)
    rh_min = min(mock_rhs)
    rh_max = max(mock_rhs)

    if len(result["summaries"]) == 0:
        assert result["summaries"] == []

    if len(result["summaries"]) == 1:
        summary = result["summaries"][0]
        assert summary["station"]["code"] == codes[0]
        assert summary["values"] == [
            {
                "datetime": weather_date.isoformat().replace("+00:00", "Z"),
                "tmp_min": tmp_min,
                "tmp_max": tmp_max,
                "rh_min": rh_min,
                "rh_max": rh_max,
            }
        ]
