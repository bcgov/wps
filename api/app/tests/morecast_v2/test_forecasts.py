from datetime import datetime
from typing import Optional
from unittest.mock import Mock, patch
import pytest
from app.db.models.morecast_v2 import MorecastForecastRecord
from app.morecast_v2.forecasts import construct_wf1_forecast, construct_wf1_forecasts, get_forecasts
from app.schemas.morecast_v2 import StationDailyFromWF1, WF1ForecastRecordType, WF1PostForecast
from app.wildfire_one.schema_parsers import WFWXWeatherStation

start_time = datetime(2022, 1, 1)
end_time = datetime(2022, 1, 2)

station_1_url = 'https://wf1/wfwx-fireweather-api/v1/stations/1'
station_2_url = 'https://wf1/wfwx-fireweather-api/v1/stations/2'

morecast_record_1 = MorecastForecastRecord(id=1,
                                           station_code=1,
                                           for_date=start_time,
                                           temp=1,
                                           rh=1,
                                           precip=1,
                                           wind_speed=1,
                                           wind_direction=1,
                                           create_timestamp=start_time,
                                           create_user='test1',
                                           update_timestamp=start_time,
                                           update_user='test1')

morecast_record_2 = MorecastForecastRecord(id=2,
                                           station_code=2,
                                           for_date=start_time,
                                           temp=2,
                                           rh=2,
                                           precip=2,
                                           wind_speed=2,
                                           wind_direction=2,
                                           create_timestamp=end_time,
                                           create_user='test2',
                                           update_timestamp=end_time,
                                           update_user='test2')

wfwx_weather_stations = [
    WFWXWeatherStation(
        wfwx_id='1',
        code=1,
        name='station1',
        latitude=12.1,
        longitude=12.1,
        elevation=123,
        zone_code=1
    ),
    WFWXWeatherStation(
        wfwx_id='2',
        code=2,
        name='station2',
        latitude=12.2,
        longitude=12.2,
        elevation=123.2,
        zone_code=2
    )
]

station_1_daily_from_wf1 = StationDailyFromWF1(created_by='test',
                                               forecast_id='f1',
                                               station_code=1,
                                               station_name='station1',
                                               utcTimestamp=start_time)


def assert_wf1_forecast(result: WF1PostForecast,
                        morecast_record_1: MorecastForecastRecord,
                        expected_id: Optional[str],
                        expected_created_by: Optional[str],
                        expected_station_url: str,
                        expected_station_id: str):
    assert result.id == expected_id
    assert result.createdBy == expected_created_by
    assert result.station == expected_station_url
    assert result.stationId == expected_station_id
    assert result.temperature == morecast_record_1.temp
    assert result.relativeHumidity == morecast_record_1.rh
    assert result.precipitation == morecast_record_1.precip
    assert result.windSpeed == morecast_record_1.wind_speed
    assert result.windDirection == morecast_record_1.wind_direction
    assert result.weatherTimestamp == datetime.timestamp(morecast_record_1.for_date) * 1000
    assert result.recordType == WF1ForecastRecordType()


@patch('app.morecast_v2.forecasts.get_forecasts_in_range', return_value=[])
def test_get_forecasts_empty(_):
    result = get_forecasts(Mock(), start_time, end_time, [])
    assert len(result) == 0


@patch('app.morecast_v2.forecasts.get_forecasts_in_range', return_value=[morecast_record_1, morecast_record_2])
def test_get_forecasts_non_empty(_):
    result = get_forecasts(Mock(), start_time, end_time, [1, 2])
    assert len(result) == 2
    assert result[0].station_code == 1
    assert result[1].station_code == 2


def test_construct_wf1_forecast_new():
    result = construct_wf1_forecast(morecast_record_1,
                                    wfwx_weather_stations,
                                    None,
                                    'test')
    assert_wf1_forecast(result, morecast_record_1, None, 'test', station_1_url, '1')


def test_construct_wf1_forecast_update():
    result = construct_wf1_forecast(morecast_record_1,
                                    wfwx_weather_stations,
                                    'f1',
                                    'test')
    assert_wf1_forecast(result, morecast_record_1, 'f1', 'test', station_1_url, '1')


@pytest.mark.anyio
@patch('aiohttp.ClientSession.get')
@patch('app.morecast_v2.forecasts.get_forecasts_for_stations_by_date_range', return_value=[station_1_daily_from_wf1])
async def test_construct_wf1_forecasts_new(_, mock_get):
    result = await construct_wf1_forecasts(mock_get,
                                           [morecast_record_1, morecast_record_2],
                                           wfwx_weather_stations)
    assert len(result) == 2
    # existing forecast
    assert_wf1_forecast(result[0], morecast_record_1,
                        station_1_daily_from_wf1.forecast_id,
                        station_1_daily_from_wf1.created_by,
                        station_1_url, '1')
    # no existing forecast
    assert_wf1_forecast(result[1],
                        morecast_record_2,
                        None,
                        None,
                        station_2_url, '2')
