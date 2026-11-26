from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from wps_shared.schemas.morecast_v2 import (
    WeatherDeterminate,
    WeatherIndeterminate,
)
from wps_shared.schemas.stations import WeatherStation
from wps_shared.weather_models.fetch import predictions
from wps_shared.weather_models.fetch.predictions import post_process_fetched_predictions


def build_weather_indeterminate(
    station_code: int, station_name: str, determinate: WeatherDeterminate, utc_timestamp: datetime
):
    return WeatherIndeterminate(
        station_code=station_code,
        station_name=station_name,
        determinate=determinate,
        utc_timestamp=utc_timestamp,
    )


def test_post_process_fetched_predictions_empty():
    assert post_process_fetched_predictions([]) == []


def test_post_process_fetched_predictions_same_everything():
    weather_indeterminates = [
        build_weather_indeterminate(
            1, "one", WeatherDeterminate.GDPS, utc_timestamp=datetime(2023, 1, 1)
        ),
        build_weather_indeterminate(
            1, "one", WeatherDeterminate.GDPS, utc_timestamp=datetime(2023, 1, 1)
        ),
    ]
    assert post_process_fetched_predictions(weather_indeterminates) == [weather_indeterminates[0]]


def test_post_process_fetched_predictions_same_station_date_different_model():
    weather_indeterminates = [
        build_weather_indeterminate(
            1, "one", WeatherDeterminate.GDPS, utc_timestamp=datetime(2023, 1, 1)
        ),
        build_weather_indeterminate(
            1, "one", WeatherDeterminate.HRDPS, utc_timestamp=datetime(2023, 1, 1)
        ),
    ]
    assert post_process_fetched_predictions(weather_indeterminates) == weather_indeterminates


def test_post_process_fetched_predictions_same_station_model_different_date():
    weather_indeterminates = [
        build_weather_indeterminate(
            1, "one", WeatherDeterminate.GDPS, utc_timestamp=datetime(2023, 1, 1)
        ),
        build_weather_indeterminate(
            1, "one", WeatherDeterminate.GDPS, utc_timestamp=datetime(2023, 1, 2)
        ),
    ]
    assert post_process_fetched_predictions(weather_indeterminates) == weather_indeterminates


def test_post_process_fetched_predictions_same_date_model_different_station():
    weather_indeterminates = [
        build_weather_indeterminate(
            1, "one", WeatherDeterminate.GDPS, utc_timestamp=datetime(2023, 1, 1)
        ),
        build_weather_indeterminate(
            2, "two", WeatherDeterminate.GDPS, utc_timestamp=datetime(2023, 1, 1)
        ),
    ]
    assert post_process_fetched_predictions(weather_indeterminates) == weather_indeterminates


def test_post_process_fetched_predictions_different_everything():
    weather_indeterminates = [
        build_weather_indeterminate(
            1, "one", WeatherDeterminate.GDPS, utc_timestamp=datetime(2023, 1, 1)
        ),
        build_weather_indeterminate(
            2, "two", WeatherDeterminate.HRDPS, utc_timestamp=datetime(2023, 1, 2)
        ),
    ]
    assert post_process_fetched_predictions(weather_indeterminates) == weather_indeterminates


def build_prediction_row(
    model: str,
    model_elevation: float | None,
    run_timestamp: datetime,
    station_code: int = 1,
    prediction_timestamp: datetime = datetime(2023, 1, 1, 20, tzinfo=timezone.utc),
) -> tuple:
    return (
        prediction_timestamp,
        model,
        run_timestamp,
        station_code,
        40.0,
        20.0,
        22.0,
        42.0,
        12.0,
        190.0,
        1.0,
        2.0,
        180.0,
        10.0,
        model_elevation,
    )


@pytest.mark.parametrize(
    "model,model_elevation",
    [("HRDPS", 1234.57), ("RDPS", 0.0), ("GDPS", None), ("GFS", 567.89), ("ECMWF", 1049.75)],
)
def test_fetch_predictions_includes_elevation_only_on_raw_model_records(
    monkeypatch: pytest.MonkeyPatch, model: str, model_elevation: float | None
) -> None:
    run_timestamp = datetime(2023, 1, 1, tzinfo=timezone.utc)
    query = Mock(return_value=[build_prediction_row(model, model_elevation, run_timestamp)])
    monkeypatch.setattr(predictions, "get_latest_station_prediction", query)
    stations = [WeatherStation(code=1, name="Station one", lat=51, long=-121)]

    results = predictions.fetch_latest_model_run_predictions_by_station_code_and_date_range(
        Mock(), stations, run_timestamp, run_timestamp
    )

    assert [(row.determinate.value, row.temperature, row.model_elevation) for row in results] == [
        (model, 20.0, model_elevation),
        (f"{model}_BIAS", 22.0, None),
    ]
    assert all(row.prediction_run_timestamp == run_timestamp for row in results)
    query.assert_called_once()


def test_fetch_predictions_keeps_elevation_with_selected_run_and_station(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old_run = datetime(2023, 1, 1, tzinfo=timezone.utc)
    new_run = old_run.replace(hour=12)
    query = Mock(
        return_value=[
            build_prediction_row("HRDPS", 1234.57, new_run),
            build_prediction_row("HRDPS", 999.99, old_run),
            build_prediction_row("HRDPS", 0.0, new_run, station_code=2),
            build_prediction_row("ECMWF", 500.0, new_run),
        ]
    )
    monkeypatch.setattr(predictions, "get_latest_station_prediction", query)
    stations = [
        WeatherStation(code=1, name="Station one", lat=51, long=-121),
        WeatherStation(code=2, name="Station two", lat=52, long=-122),
    ]

    results = predictions.fetch_latest_model_run_predictions_by_station_code_and_date_range(
        Mock(), stations, old_run, old_run
    )

    assert len(results) == 6
    assert all(row.prediction_run_timestamp == new_run for row in results)
    assert {
        (row.station_code, row.determinate.value): row.model_elevation
        for row in results
        if not row.determinate.value.endswith("_BIAS")
    } == {(1, "HRDPS"): 1234.57, (2, "HRDPS"): 0.0, (1, "ECMWF"): 500.0}
    assert all(
        row.model_elevation is None for row in results if row.determinate.value.endswith("_BIAS")
    )


@pytest.mark.parametrize("same_run", [True, False])
def test_fetch_predictions_preserves_elevations_for_each_forecast_date(
    monkeypatch: pytest.MonkeyPatch, same_run: bool
) -> None:
    first_day = datetime(2023, 1, 1, tzinfo=timezone.utc)
    second_day = datetime(2023, 1, 2, tzinfo=timezone.utc)
    second_run = first_day if same_run else second_day
    second_elevation = 1234.57 if same_run else 1250.0
    query = Mock(
        side_effect=[
            [build_prediction_row("HRDPS", 1234.57, first_day)],
            [
                build_prediction_row(
                    "HRDPS",
                    second_elevation,
                    second_run,
                    prediction_timestamp=second_day.replace(hour=20),
                )
            ],
        ]
    )
    monkeypatch.setattr(predictions, "get_latest_station_prediction", query)
    stations = [WeatherStation(code=1, name="Station one", lat=51, long=-121)]

    results = predictions.fetch_latest_model_run_predictions_by_station_code_and_date_range(
        Mock(), stations, first_day, second_day
    )

    assert len(results) == 4
    assert [
        (row.utc_timestamp.date(), row.prediction_run_timestamp, row.model_elevation)
        for row in results
        if row.determinate == WeatherDeterminate.HRDPS
    ] == [
        (first_day.date(), first_day, 1234.57),
        (second_day.date(), second_run, second_elevation),
    ]
    assert all(
        row.model_elevation is None
        for row in results
        if row.determinate == WeatherDeterminate.HRDPS_BIAS
    )
    assert query.call_count == 2


def test_fetch_predictions_returns_empty_list_without_predictions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(predictions, "get_latest_station_prediction", Mock(return_value=[]))
    run_timestamp = datetime(2023, 1, 1, tzinfo=timezone.utc)
    stations = [WeatherStation(code=1, name="Station one", lat=51, long=-121)]

    results = predictions.fetch_latest_model_run_predictions_by_station_code_and_date_range(
        Mock(), stations, run_timestamp, run_timestamp
    )

    assert results == []
