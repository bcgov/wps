from app.schemas.morecast_v2 import WeatherDeterminate, WeatherIndeterminate
from datetime import datetime
from app.weather_models.fetch.predictions import post_process_fetched_predictions


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


def test_post_process_fetched_predictions_empty():
    assert post_process_fetched_predictions([]) == []


def test_post_process_fetched_predictions_same_everything():
    weather_indeterminates = [
        build_weather_indeterminate(1, "one", WeatherDeterminate.GDPS, utc_timestamp=datetime(2023, 1, 1)),
        build_weather_indeterminate(1, "one", WeatherDeterminate.GDPS, utc_timestamp=datetime(2023, 1, 1))
    ]
    assert post_process_fetched_predictions(weather_indeterminates) == [weather_indeterminates[0]]


def test_post_process_fetched_predictions_same_station_date_different_model():
    weather_indeterminates = [
        build_weather_indeterminate(1, "one", WeatherDeterminate.GDPS, utc_timestamp=datetime(2023, 1, 1)),
        build_weather_indeterminate(1, "one", WeatherDeterminate.HRDPS, utc_timestamp=datetime(2023, 1, 1))
    ]
    assert post_process_fetched_predictions(weather_indeterminates) == weather_indeterminates


def test_post_process_fetched_predictions_same_station_model_different_date():
    weather_indeterminates = [
        build_weather_indeterminate(1, "one", WeatherDeterminate.GDPS, utc_timestamp=datetime(2023, 1, 1)),
        build_weather_indeterminate(1, "one", WeatherDeterminate.GDPS, utc_timestamp=datetime(2023, 1, 2))
    ]
    assert post_process_fetched_predictions(weather_indeterminates) == weather_indeterminates


def test_post_process_fetched_predictions_same_date_model_different_station():
    weather_indeterminates = [
        build_weather_indeterminate(1, "one", WeatherDeterminate.GDPS, utc_timestamp=datetime(2023, 1, 1)),
        build_weather_indeterminate(2, "two", WeatherDeterminate.GDPS, utc_timestamp=datetime(2023, 1, 1))
    ]
    assert post_process_fetched_predictions(weather_indeterminates) == weather_indeterminates


def test_post_process_fetched_predictions_different_everything():
    weather_indeterminates = [
        build_weather_indeterminate(1, "one", WeatherDeterminate.GDPS, utc_timestamp=datetime(2023, 1, 1)),
        build_weather_indeterminate(2, "two", WeatherDeterminate.HRDPS, utc_timestamp=datetime(2023, 1, 2))
    ]
    assert post_process_fetched_predictions(weather_indeterminates) == weather_indeterminates
