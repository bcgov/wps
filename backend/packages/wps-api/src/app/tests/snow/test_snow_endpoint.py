import pytest
from aiohttp import ClientSession
from datetime import date, datetime, timezone
from starlette.testclient import TestClient
import app.main
from wps_shared.db.models.snow import ProcessedSnow, SnowSourceEnum
from wps_shared.tests.common import default_mock_client_get


DATE_OF_INTEREST = date(2025, 3, 12)
FOR_DATE = datetime(2025, 3, 10, tzinfo=timezone.utc)
PROCESSED_DATE = datetime(2025, 3, 12, tzinfo=timezone.utc)
PROCESSED_SNOW = ProcessedSnow(id=1, for_date=FOR_DATE, processed_date=PROCESSED_DATE, snow_source=SnowSourceEnum.viirs)


@pytest.fixture()
def mock_database(monkeypatch):
    """ Mock out call to DB returning last processed snow record """
    async def mock_get_most_processed_snow_by_date(*args, **kwargs):
        return [PROCESSED_SNOW]
    monkeypatch.setattr(app.routers.snow, 'get_most_recent_processed_snow_by_date', mock_get_most_processed_snow_by_date)

@pytest.mark.usefixtures("mock_jwt_decode")
def test_most_recent_snow_by_date_endpoint(mock_database, monkeypatch):
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    client = TestClient(app.main.app)
    headers = {"Content-Type": "application/json", "Authorization": "Bearer token"}
    response = client.get(f"api/snow/most-recent-by-date/{DATE_OF_INTEREST.isoformat()}", headers=headers)
    result = response.json()
    processed_snow_result = result['processed_snow']
    assert len(result) == 1
    assert response.status_code == 200
    assert processed_snow_result['for_date'] == FOR_DATE.strftime("%Y-%m-%dT%H:%M:%SZ")
    assert processed_snow_result['processed_date'] == PROCESSED_DATE.strftime("%Y-%m-%dT%H:%M:%SZ")
    assert processed_snow_result['snow_source'] == SnowSourceEnum.viirs.value
