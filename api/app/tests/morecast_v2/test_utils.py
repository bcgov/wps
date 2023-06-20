from app.schemas.morecast_v2 import WeatherDeterminate, WeatherIndeterminate
from app.morecast_v2.util import actual_exists
from datetime import datetime


def build_weather_indeterminate(station_code: int,
                                station_name: str,
                                determinate: WeatherDeterminate,
                                utc_timestamp: datetime):
    return WeatherIndeterminate(
        station_code=station_code,
        station_name=station_name,
        determinate=determinate,
        utc_timestamp=utc_timestamp
    )


def create_list_of_actuals():
    actual_1 = build_weather_indeterminate(1, "test1", WeatherDeterminate.ACTUAL, datetime(2023, 1, 1))
    actual_2 = build_weather_indeterminate(2, "test2", WeatherDeterminate.ACTUAL, datetime(2023, 1, 1))
    return [actual_1, actual_2]


def test_returns_true_if_station_code_and_timestamp_match():
    actuals = create_list_of_actuals()
    api_forecast = build_weather_indeterminate(1, "test1", WeatherDeterminate.FORECAST, datetime(2023, 1, 1))
    assert actual_exists(api_forecast, actuals) == True


def test_returns_false_if_no_station_codes_matches():
    actuals = create_list_of_actuals()
    api_forecast = build_weather_indeterminate(3, "test3", WeatherDeterminate.FORECAST, datetime(2023, 1, 1))
    assert actual_exists(api_forecast, actuals) == False


def test_returns_false_if_station_matches_but_no_timestamp_match():
    actuals = create_list_of_actuals()
    api_forecast = build_weather_indeterminate(1, "test1", WeatherDeterminate.FORECAST, datetime(2023, 1, 2))
    assert actual_exists(api_forecast, actuals) == False


def test_returns_false_if_no_station_code_match_and_no_timestamp_match():
    actuals = create_list_of_actuals()
    api_forecast = build_weather_indeterminate(3, "test1", WeatherDeterminate.FORECAST, datetime(2023, 1, 2))
    assert actual_exists(api_forecast, actuals) == False


def test_returns_false_if_no_actuals():
    actuals = []
    api_forecast = build_weather_indeterminate(3, "test1", WeatherDeterminate.FORECAST, datetime(2023, 1, 2))
    assert actual_exists(api_forecast, actuals) == False
