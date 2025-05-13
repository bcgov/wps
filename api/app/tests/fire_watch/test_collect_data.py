import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from app.fire_watch.calculate_weather import (
    FIREWATCH_WEATHER_MODEL,
    get_station_metadata,
    map_model_prediction_to_weather_indeterminate,
)
from wps_shared.schemas.morecast_v2 import WeatherDeterminate, WeatherIndeterminate
from wps_shared.schemas.weather_models import ModelPredictionDetails
from wps_shared.wildfire_one.schema_parsers import WFWXWeatherStation


@pytest.mark.anyio
async def test_map_model_prediction_to_weather_indeterminate():
    model_prediction = ModelPredictionDetails(
        station_code=1,
        abbreviation=FIREWATCH_WEATHER_MODEL.value,
        prediction_timestamp=datetime(2025, 4, 25, 20, tzinfo=timezone.utc),
        tmp_tgl_2=25.0,
        rh_tgl_2=50.0,
        precip_24h=5.0,
        wdir_tgl_10=180.0,
        wind_tgl_10=10.0,
        update_date=datetime(2025, 4, 25, 14, tzinfo=timezone.utc),
        prediction_run_timestamp=datetime(2025, 4, 25, 12, tzinfo=timezone.utc),
        prediction_model_run_timestamp_id=1234,
    )
    station_details = WFWXWeatherStation(code=1, name="Station 1", lat=50.0, long=-120.0, elevation=1, wfwx_id="1", zone_code=None)
    result = map_model_prediction_to_weather_indeterminate(model_prediction, station_details)
    assert result.station_code == 1
    assert result.station_name == "Station 1"
    assert result.temperature == pytest.approx(25.0)
    assert result.relative_humidity == pytest.approx(50.0)
    assert result.precipitation == pytest.approx(5.0)
    assert result.wind_direction == pytest.approx(180.0)
    assert result.wind_speed == pytest.approx(10.0)
    assert result.utc_timestamp == datetime(2025, 4, 25, 20, tzinfo=timezone.utc)
    assert result.update_date == datetime(2025, 4, 25, 14, tzinfo=timezone.utc)
    assert result.prediction_run_timestamp == datetime(2025, 4, 25, 12, tzinfo=timezone.utc)


@pytest.mark.anyio
@patch("app.fire_watch.calculate_weather.get_auth_header", new_callable=AsyncMock)
@patch("app.fire_watch.calculate_weather.get_wfwx_stations_from_station_codes", new_callable=AsyncMock)
async def test_fetch_station_metadata(mock_get_stations, mock_get_auth_header):
    mock_get_stations.return_value = [WFWXWeatherStation(code=1, name="Station 1", lat=50.0, long=-120.0, elevation=1, wfwx_id="1", zone_code=None)]
    result = await get_station_metadata([1])
    assert result[1].name == "Station 1"
