from datetime import datetime
from unittest.mock import Mock, patch
from app.db.models.morecast_v2 import MorecastForecastRecord
from app.morecast_v2.forecasts import construct_wf1_forecast, get_forecasts
from app.schemas.morecast_v2 import WF1ForecastRecordType
from app.wildfire_one.schema_parsers import WFWXWeatherStation

start_time = datetime(2022, 1, 1)
end_time = datetime(2022, 1, 2)

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
        zone_code=1)
]


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
    assert result.id is None
    assert result.createdBy == 'test'
    assert result.station == 'https://wf1/wfwx-fireweather-api/v1/stations/1'
    assert result.stationId == '1'
    assert result.temperature == morecast_record_1.temp
    assert result.relativeHumidity == morecast_record_1.rh
    assert result.precipitation == morecast_record_1.precip
    assert result.windSpeed == morecast_record_1.wind_speed
    assert result.windDirection == morecast_record_1.wind_direction
    assert result.weatherTimestamp == datetime.timestamp(morecast_record_1.for_date) * 1000
    assert result.recordType == WF1ForecastRecordType()


def test_construct_wf1_forecast_update():
    result = construct_wf1_forecast(morecast_record_1,
                                    wfwx_weather_stations,
                                    'f1',
                                    'test')
    assert result.id == 'f1'
    assert result.createdBy == 'test'
    assert result.station == 'https://wf1/wfwx-fireweather-api/v1/stations/1'
    assert result.stationId == '1'
    assert result.temperature == morecast_record_1.temp
    assert result.relativeHumidity == morecast_record_1.rh
    assert result.precipitation == morecast_record_1.precip
    assert result.windSpeed == morecast_record_1.wind_speed
    assert result.windDirection == morecast_record_1.wind_direction
    assert result.weatherTimestamp == datetime.timestamp(morecast_record_1.for_date) * 1000
    assert result.recordType == WF1ForecastRecordType()
