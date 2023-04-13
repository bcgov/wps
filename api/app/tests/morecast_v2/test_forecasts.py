from datetime import datetime
from unittest.mock import Mock, patch
from app.db.models.morecast_v2 import MorecastForecastRecord
from app.morecast_v2.forecasts import get_forecasts

start_time = datetime(2022, 1, 1)
end_time = datetime(2022, 1, 2)


@patch('app.morecast_v2.forecasts.get_forecasts_in_range', return_value=[])
def test_get_forecasts_empty(_):
    result = get_forecasts(Mock(), start_time, end_time, [])
    assert len(result) == 0


@patch('app.morecast_v2.forecasts.get_forecasts_in_range', return_value=[
    MorecastForecastRecord(id=1,
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
                           update_user='test1'),
    MorecastForecastRecord(id=2,
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
                           update_user='test2')])
def test_get_forecasts_non_empty(_):
    result = get_forecasts(Mock(), start_time, end_time, [1, 2])
    assert len(result) == 2
    assert result[0].station_code == 1
    assert result[1].station_code == 2
