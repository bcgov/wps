from app.morecast_v2.determinates import get_all_disjoint_determinates

from datetime import datetime
from app.schemas.morecast_v2 import WeatherDeterminate, WeatherIndeterminate


def build_weather_indeterminate(station_code: int, station_name: str, determinate: WeatherDeterminate, utc_timestamp: datetime):
    return WeatherIndeterminate(station_code=station_code,
                                station_name=station_name,
                                determinate=determinate,
                                utcTimestamp=utc_timestamp)


def test_get_all_disjoint_determinates_empty_input():
    # Test with empty actuals and predictions
    actuals = []
    predictions = []
    result = get_all_disjoint_determinates(actuals, predictions)
    assert result.size() == 0


def test_get_all_disjoint_determinates_empty_predictions():
    actuals = [build_weather_indeterminate(1, "one", WeatherDeterminate.ACTUAL, datetime(2022, 1, 1))]
    result = get_all_disjoint_determinates(actuals, [])
    assert result.get_flat_actuals() == actuals
    assert result.get_flat_predictions() == []


def test_get_all_disjoint_determinates_empty_actuals():
    predictions = [build_weather_indeterminate(1, "one", WeatherDeterminate.GDPS, datetime(2022, 1, 1))]
    result = get_all_disjoint_determinates([], predictions)
    assert result.get_flat_actuals() == []
    assert result.get_flat_predictions() == predictions


def test_get_all_disjoint_determinates_already_disjoint():
    station_1_actuals = [build_weather_indeterminate(1, "one", WeatherDeterminate.ACTUAL, datetime(2022, 1, 1))]
    station_1_predictions = [build_weather_indeterminate(1, "one", WeatherDeterminate.GDPS, datetime(2022, 1, 2))]
    result = get_all_disjoint_determinates(station_1_actuals, station_1_predictions)
    assert result.get_flat_predictions() == station_1_predictions
    assert result.get_flat_actuals() == station_1_actuals


def test_get_all_disjoint_determinates_non_disjoint_with_actual_precedence():
    station_1_actuals = [build_weather_indeterminate(1, "one", WeatherDeterminate.ACTUAL, datetime(2022, 1, 1))]
    station_1_predictions = [build_weather_indeterminate(1, "one", WeatherDeterminate.GDPS, datetime(2022, 1, 1))]
    result = get_all_disjoint_determinates(station_1_actuals, station_1_predictions)
    assert result.get_flat_predictions() == []
    assert result.get_flat_actuals() == station_1_actuals


def test_get_all_disjoint_determinates_non_disjoint_multiple_stations():
    station_1_actuals = [
        build_weather_indeterminate(1, "one", WeatherDeterminate.ACTUAL, datetime(2022, 1, 1)),
        build_weather_indeterminate(2, "two", WeatherDeterminate.ACTUAL, datetime(2022, 1, 1))

    ]
    station_1_predictions = [
        build_weather_indeterminate(1, "one", WeatherDeterminate.GDPS, datetime(2022, 1, 1)),
        build_weather_indeterminate(2, "two", WeatherDeterminate.GDPS, datetime(2022, 1, 1))
    ]
    result = get_all_disjoint_determinates(station_1_actuals, station_1_predictions)
    assert result.get_flat_predictions() == []
    assert result.get_flat_actuals() == station_1_actuals


def test_get_all_disjoint_determinates_disjoint_multiple_stations():
    station_1_actuals = [
        build_weather_indeterminate(1, "one", WeatherDeterminate.ACTUAL, datetime(2022, 1, 1)),
        build_weather_indeterminate(2, "two", WeatherDeterminate.ACTUAL, datetime(2022, 1, 1))

    ]
    station_1_predictions = [
        build_weather_indeterminate(1, "one", WeatherDeterminate.GDPS, datetime(2022, 1, 2)),
        build_weather_indeterminate(2, "two", WeatherDeterminate.GDPS, datetime(2022, 1, 2))
    ]
    result = get_all_disjoint_determinates(station_1_actuals, station_1_predictions)
    assert result.get_flat_predictions() == station_1_predictions
    assert result.get_flat_actuals() == station_1_actuals
