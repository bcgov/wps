import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from app.fire_watch.collect_weather import (
    map_model_prediction_to_weather_indeterminate,
    collect_fire_weather_data,
    fetch_station_metadata,
    fetch_actuals_and_forecasts,
    prepare_data_for_fwi,
    marshal_weather_data_to_api,
)
from wps_shared.schemas.morecast_v2 import WeatherDeterminate, WeatherIndeterminate
from wps_shared.schemas.weather_models import ModelPredictionDetails
from wps_shared.wildfire_one.schema_parsers import WFWXWeatherStation


@pytest.mark.anyio
async def test_map_model_prediction_to_weather_indeterminate():
    model_prediction = ModelPredictionDetails(
        station_code=1,
        abbreviation="GFS",
        prediction_timestamp=datetime(2025, 4, 25, 20, tzinfo=timezone.utc),
        tmp_tgl_2=25.0,
        rh_tgl_2=50.0,
        precip_24h=5.0,
        wdir_tgl_10=180.0,
        wind_tgl_10=10.0,
        update_date=datetime(2025, 4, 25, 14, tzinfo=timezone.utc),
        prediction_run_timestamp=datetime(2025, 4, 25, 12, tzinfo=timezone.utc),
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
@patch("app.fire_watch.collect_weather.get_auth_header", new_callable=AsyncMock)
@patch("app.fire_watch.collect_weather.get_wfwx_stations_from_station_codes", new_callable=AsyncMock)
async def test_fetch_station_metadata(mock_get_stations, mock_get_auth):
    mock_get_stations.return_value = [WFWXWeatherStation(code=1, name="Station 1", lat=50.0, long=-120.0, elevation=1, wfwx_id="1", zone_code=None)]
    result = await fetch_station_metadata([1])
    assert result[1].name == "Station 1"


def test_prepare_data_for_fwi():
    wf1_actuals = [WeatherIndeterminate(station_code=1, station_name="Station 1", utc_timestamp=datetime(2025, 4, 25, tzinfo=timezone.utc), determinate=WeatherDeterminate.ACTUAL)]
    wf1_forecasts = [WeatherIndeterminate(station_code=1, station_name="Station 1", utc_timestamp=datetime(2025, 4, 26, tzinfo=timezone.utc), determinate=WeatherDeterminate.FORECAST)]
    predictions = [
        ModelPredictionDetails(
            prediction_timestamp=datetime(2025, 4, 27, tzinfo=timezone.utc),
            station_code=1,
            abbreviation="GFS",
            update_date=datetime(2025, 4, 25, 14, tzinfo=timezone.utc),
            prediction_run_timestamp=datetime(2025, 4, 25, 12, tzinfo=timezone.utc),
        ),
        ModelPredictionDetails(
            prediction_timestamp=datetime(2025, 4, 28, tzinfo=timezone.utc),
            station_code=1,
            abbreviation="GFS",
            update_date=datetime(2025, 4, 25, 14, tzinfo=timezone.utc),
            prediction_run_timestamp=datetime(2025, 4, 25, 12, tzinfo=timezone.utc),
        ),
    ]
    wfwx_station_map = {1: WFWXWeatherStation(code=1, name="Station 1", lat=50.0, long=-120.0, elevation=1, wfwx_id="1", zone_code=None)}
    actuals_forecasts, predictions = prepare_data_for_fwi(wf1_actuals, wf1_forecasts, predictions, wfwx_station_map, [1], datetime(2025, 4, 25), datetime(2025, 4, 29))
    assert len(actuals_forecasts) == 2
    assert len(predictions) == 2
    assert predictions[0].utc_timestamp == datetime(2025, 4, 27, tzinfo=timezone.utc)


def test_marshal_weather_data_to_api():
    actuals_forecasts = [WeatherIndeterminate(station_code=1, station_name="Station 1", utc_timestamp=datetime(2025, 4, 25, tzinfo=timezone.utc), determinate="Actual")]
    predictions = []
    result = marshal_weather_data_to_api(actuals_forecasts, predictions)
    assert len(result[1]) == 1
