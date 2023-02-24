from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
import pytest
import app.routers.weather_models
from app.schemas.shared import ModelDataRequest
from app.weather_models import ModelEnum

model_data_request = ModelDataRequest(stations=[1, 2])


@pytest.fixture()
def client():
    from app.main import app as test_app

    with TestClient(test_app) as test_client:
        yield test_client


def test_post_forecast_unauthorized_date_range(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """ requests model date by user and date range unauthorized """

    monkeypatch.setattr(app.routers.weather_models,
                        'fetch_latest_daily_model_run_predictions_by_station_code_and_date_range', lambda *_: [])

    for model in ModelEnum:
        weather_models_post_url = f'/api/weather_models/{model.value}/predictions/most_recent/2022-09-01/2022-09-02'
        response = client.post(weather_models_post_url, json=model_data_request.dict())
        assert response.status_code == 401


@pytest.mark.usefixtures("mock_jwt_decode")
def test_post_forecast_authorized_date_range(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """ requests model date by user and date range authorized """

    mock_predictions = AsyncMock()
    mock_predictions.return_value = []

    monkeypatch.setattr(app.routers.weather_models,
                        'fetch_latest_daily_model_run_predictions_by_station_code_and_date_range', mock_predictions)

    for model in ModelEnum:
        weather_models_post_url = f'/api/weather_models/{model.value}/predictions/most_recent/2022-09-01/2022-09-02'
        response = client.post(weather_models_post_url, json=model_data_request.dict())
        assert response.status_code == 200
