import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
import app
from wps_shared.schemas.fire_watch import FireWatchFireCentre, FireWatchOutput
from wps_shared.schemas.stations import GeoJsonWeatherStation
from app.routers.fire_watch import (
    create_fire_watch_output,
    update_existing_fire_watch,
    MissingWeatherDataError,
)


@pytest.fixture
def fire_watch_input_request():
    mock_fire_watch = MagicMock()
    mock_fire_watch_input = MagicMock()
    mock_fire_watch_input.fire_watch = mock_fire_watch
    return mock_fire_watch_input


@pytest.fixture
def token():
    return {"idir_username": "testuser"}


@pytest.fixture
def mock_stations():
    return [
        GeoJsonWeatherStation(
            type="Feature",
            geometry={"type": "Point", "coordinates": [-120.0, 50.0]},
            properties={"code": 101, "name": "Test Station"},
        )
    ]


@pytest.fixture
def mock_fire_centre():
    return FireWatchFireCentre(id=1, name="Test Fire Centre")


@pytest.mark.anyio
@patch("app.routers.fire_watch.get_async_write_session_scope")
@patch("app.routers.fire_watch.marshall_fire_watch_input_to_db")
@patch("app.routers.fire_watch.get_fire_watch_by_id", new_callable=AsyncMock)
@patch("app.routers.fire_watch.update_fire_watch", new_callable=AsyncMock)
@patch(
    "app.routers.fire_watch.get_latest_processed_model_run_id_in_fire_watch_weather",
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
    fire_watch_input_request,
    token,
    mocker,
    mock_wfwx_api,
):
    # Setup mocks
    mock_wfwx_api.get_stations_as_geojson.return_value = ["station"]
    mocker.patch("app.routers.fire_watch.WfwxApi", return_value=mock_wfwx_api)
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
@patch("app.routers.fire_watch.get_async_write_session_scope")
@patch("app.routers.fire_watch.marshall_fire_watch_input_to_db")
@patch("app.routers.fire_watch.get_fire_watch_by_id", new_callable=AsyncMock)
async def test_update_existing_fire_watch_not_found(
    mock_get_by_id,
    mock_marshall,
    mock_session_scope,
    fire_watch_input_request,
    token,
    mocker,
    mock_wfwx_api,
):
    mock_wfwx_api.get_stations_as_geojson.return_value = ["station"]
    mocker.patch("app.routers.fire_watch.WfwxApi", return_value=mock_wfwx_api)
    mock_session = AsyncMock()
    mock_session_scope.return_value.__aenter__.return_value = mock_session
    mock_get_by_id.return_value = None
    mock_marshall.return_value = MagicMock()

    with pytest.raises(HTTPException) as exc:
        await update_existing_fire_watch(1, fire_watch_input_request, token)
    assert exc.value.status_code == 404
    assert "not found" in exc.value.detail


@pytest.mark.anyio
@patch("app.routers.fire_watch.get_async_write_session_scope")
@patch("app.routers.fire_watch.marshall_fire_watch_input_to_db")
@patch("app.routers.fire_watch.get_fire_watch_by_id", new_callable=AsyncMock)
@patch("app.routers.fire_watch.update_fire_watch", new_callable=AsyncMock)
@patch(
    "app.routers.fire_watch.get_latest_processed_model_run_id_in_fire_watch_weather",
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
    fire_watch_input_request,
    token,
    mocker,
    mock_wfwx_api,
):
    mock_wfwx_api.get_stations_as_geojson.return_value = ["station"]
    mocker.patch("app.routers.fire_watch.WfwxApi", return_value=mock_wfwx_api)
    mock_session = AsyncMock()
    mock_session_scope.return_value.__aenter__.return_value = mock_session
    fire_watch = MagicMock(id=1)
    fire_centre = MagicMock()
    mock_get_by_id.return_value = (fire_watch, fire_centre)
    updated_fire_watch = MagicMock(id=1)
    mock_update.return_value = updated_fire_watch
    mock_get_latest_id.return_value = 123
    mock_reprocess.side_effect = MissingWeatherDataError("missing weather")
    mock_marshall.return_value = MagicMock()

    with pytest.raises(HTTPException) as exc:
        await update_existing_fire_watch(1, fire_watch_input_request, token)
    assert exc.value.status_code == 500
    assert "Missing actual weather data" in exc.value.detail


@pytest.mark.anyio
@patch("app.routers.fire_watch.get_async_write_session_scope")
@patch("app.routers.fire_watch.marshall_fire_watch_input_to_db")
@patch("app.routers.fire_watch.get_fire_watch_by_id", new_callable=AsyncMock)
@patch("app.routers.fire_watch.update_fire_watch", new_callable=AsyncMock)
@patch(
    "app.routers.fire_watch.get_latest_processed_model_run_id_in_fire_watch_weather",
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
    fire_watch_input_request,
    token,
    mocker,
    mock_wfwx_api,
):
    mock_wfwx_api.get_stations_as_geojson.return_value = ["station"]
    mocker.patch("app.routers.fire_watch.WfwxApi", return_value=mock_wfwx_api)
    mock_session = AsyncMock()
    mock_session_scope.return_value.__aenter__.return_value = mock_session
    fire_watch = MagicMock(id=1)
    fire_centre = MagicMock()
    mock_get_by_id.return_value = (fire_watch, fire_centre)
    updated_fire_watch = MagicMock(id=1)
    mock_update.return_value = updated_fire_watch
    mock_get_latest_id.return_value = 123
    mock_reprocess.side_effect = Exception("unexpected error")
    mock_marshall.return_value = MagicMock()

    with pytest.raises(HTTPException) as exc:
        await update_existing_fire_watch(1, fire_watch_input_request, token)
    assert exc.value.status_code == 500
    assert "Failed to reprocess fire watch weather" in exc.value.detail


@pytest.mark.anyio
async def test_create_fire_watch_output_success(mock_fire_watch, mock_fire_centre, mock_stations):
    result = create_fire_watch_output(mock_fire_watch, mock_fire_centre, mock_stations)

    assert isinstance(result, FireWatchOutput)
    assert result.id == mock_fire_watch.id
    assert result.fire_centre == mock_fire_centre
    assert result.station.code == 101
    assert result.station.name == "Test Station"


@pytest.mark.anyio
async def test_create_fire_watch_output_station_not_found(
    mock_fire_watch, mock_fire_centre, mock_stations
):
    # Test when station is not found in stations list, station should be None but it shouldn't raise an error
    mock_stations[0].properties.code = 999  # Different code

    result = create_fire_watch_output(mock_fire_watch, mock_fire_centre, mock_stations)

    assert result.station is None
