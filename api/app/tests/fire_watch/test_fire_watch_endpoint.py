import pytest
from unittest.mock import AsyncMock, patch, MagicMock, create_autospec
from fastapi import HTTPException
from app.routers.fire_watch import update_existing_fire_watch, MissingWeatherDataError


@pytest.fixture
def fire_watch_input_request():
    mock_fire_watch = MagicMock()
    mock_fire_watch_input = MagicMock()
    mock_fire_watch_input.fire_watch = mock_fire_watch
    return mock_fire_watch_input


@pytest.fixture
def token():
    return {"idir_username": "testuser"}


@pytest.mark.anyio
@patch("app.routers.fire_watch.get_stations_as_geojson", new_callable=AsyncMock)
@patch("app.routers.fire_watch.get_async_write_session_scope")
@patch("app.routers.fire_watch.marshall_fire_watch_input_to_db")
@patch("app.routers.fire_watch.get_fire_watch_by_id", new_callable=AsyncMock)
@patch("app.routers.fire_watch.update_fire_watch", new_callable=AsyncMock)
@patch(
    "app.routers.fire_watch.get_latest_processed_model_run_id_for_fire_watch_model",
    new_callable=AsyncMock,
)
@patch("app.routers.fire_watch.reprocess_fire_watch_weather", new_callable=AsyncMock)
@patch(
    "app.routers.fire_watch.get_fire_watch_weather_by_model_with_prescription_status",
    new_callable=AsyncMock,
)
@patch("app.routers.fire_watch.create_fire_watch_burn_forecasts_response")
async def test_update_existing_fire_watch_success(
    mock_create_burn_forecast,
    mock_get_weather,
    mock_reprocess,
    mock_get_latest_id,
    mock_update,
    mock_get_by_id,
    mock_marshall,
    mock_session_scope,
    mock_get_stations,
    fire_watch_input_request,
    token,
):
    # Setup mocks
    mock_session = AsyncMock()
    mock_session_scope.return_value.__aenter__.return_value = mock_session
    fire_watch = MagicMock(id=1)
    fire_centre = MagicMock()
    mock_get_by_id.return_value = (fire_watch, fire_centre)
    updated_fire_watch = MagicMock(id=1)
    mock_update.return_value = updated_fire_watch
    mock_get_latest_id.return_value = 123
    mock_reprocess.return_value = None
    fire_watch_weather = [("weather", "prescription")]
    mock_get_weather.return_value = fire_watch_weather
    mock_create_burn_forecast.return_value = "burn_forecast"
    mock_get_stations.return_value = ["station"]
    mock_marshall.return_value = MagicMock()

    result = await update_existing_fire_watch(1, fire_watch_input_request, token)

    assert result == "burn_forecast"
    mock_get_by_id.assert_awaited_once()
    mock_update.assert_awaited_once()
    mock_get_latest_id.assert_awaited_once()
    mock_reprocess.assert_awaited_once()
    mock_get_weather.assert_awaited_once()
    mock_create_burn_forecast.assert_called_once()


@pytest.mark.anyio
@patch("app.routers.fire_watch.get_stations_as_geojson", new_callable=AsyncMock)
@patch("app.routers.fire_watch.get_async_write_session_scope")
@patch("app.routers.fire_watch.marshall_fire_watch_input_to_db")
@patch("app.routers.fire_watch.get_fire_watch_by_id", new_callable=AsyncMock)
async def test_update_existing_fire_watch_not_found(
    mock_get_by_id,
    mock_marshall,
    mock_session_scope,
    mock_get_stations,
    fire_watch_input_request,
    token,
):
    mock_session = AsyncMock()
    mock_session_scope.return_value.__aenter__.return_value = mock_session
    mock_get_by_id.return_value = None
    mock_get_stations.return_value = ["station"]
    mock_marshall.return_value = MagicMock()

    with pytest.raises(HTTPException) as exc:
        await update_existing_fire_watch(1, fire_watch_input_request, token)
    assert exc.value.status_code == 404
    assert "not found" in exc.value.detail


@pytest.mark.anyio
@patch("app.routers.fire_watch.get_stations_as_geojson", new_callable=AsyncMock)
@patch("app.routers.fire_watch.get_async_write_session_scope")
@patch("app.routers.fire_watch.marshall_fire_watch_input_to_db")
@patch("app.routers.fire_watch.get_fire_watch_by_id", new_callable=AsyncMock)
@patch("app.routers.fire_watch.update_fire_watch", new_callable=AsyncMock)
@patch(
    "app.routers.fire_watch.get_latest_processed_model_run_id_for_fire_watch_model",
    new_callable=AsyncMock,
)
@patch("app.routers.fire_watch.reprocess_fire_watch_weather", new_callable=AsyncMock)
async def test_update_existing_fire_watch_missing_weather_data(
    mock_reprocess,
    mock_get_latest_id,
    mock_update,
    mock_get_by_id,
    mock_marshall,
    mock_session_scope,
    mock_get_stations,
    fire_watch_input_request,
    token,
):
    mock_session = AsyncMock()
    mock_session_scope.return_value.__aenter__.return_value = mock_session
    fire_watch = MagicMock(id=1)
    fire_centre = MagicMock()
    mock_get_by_id.return_value = (fire_watch, fire_centre)
    updated_fire_watch = MagicMock(id=1)
    mock_update.return_value = updated_fire_watch
    mock_get_latest_id.return_value = 123
    mock_reprocess.side_effect = MissingWeatherDataError("missing weather")
    mock_get_stations.return_value = ["station"]
    mock_marshall.return_value = MagicMock()

    with pytest.raises(HTTPException) as exc:
        await update_existing_fire_watch(1, fire_watch_input_request, token)
    assert exc.value.status_code == 500
    assert "Missing actual weather data" in exc.value.detail


@pytest.mark.anyio
@patch("app.routers.fire_watch.get_stations_as_geojson", new_callable=AsyncMock)
@patch("app.routers.fire_watch.get_async_write_session_scope")
@patch("app.routers.fire_watch.marshall_fire_watch_input_to_db")
@patch("app.routers.fire_watch.get_fire_watch_by_id", new_callable=AsyncMock)
@patch("app.routers.fire_watch.update_fire_watch", new_callable=AsyncMock)
@patch(
    "app.routers.fire_watch.get_latest_processed_model_run_id_for_fire_watch_model",
    new_callable=AsyncMock,
)
@patch("app.routers.fire_watch.reprocess_fire_watch_weather", new_callable=AsyncMock)
async def test_update_existing_fire_watch_other_exception(
    mock_reprocess,
    mock_get_latest_id,
    mock_update,
    mock_get_by_id,
    mock_marshall,
    mock_session_scope,
    mock_get_stations,
    fire_watch_input_request,
    token,
):
    mock_session = AsyncMock()
    mock_session_scope.return_value.__aenter__.return_value = mock_session
    fire_watch = MagicMock(id=1)
    fire_centre = MagicMock()
    mock_get_by_id.return_value = (fire_watch, fire_centre)
    updated_fire_watch = MagicMock(id=1)
    mock_update.return_value = updated_fire_watch
    mock_get_latest_id.return_value = 123
    mock_reprocess.side_effect = Exception("unexpected error")
    mock_get_stations.return_value = ["station"]
    mock_marshall.return_value = MagicMock()

    with pytest.raises(HTTPException) as exc:
        await update_existing_fire_watch(1, fire_watch_input_request, token)
    assert exc.value.status_code == 500
    assert "Failed to reprocess fire watch weather" in exc.value.detail
