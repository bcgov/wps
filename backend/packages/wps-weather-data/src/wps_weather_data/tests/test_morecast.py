from datetime import UTC, datetime, timedelta

import pytest
from wps_shared.schemas.morecast_v2 import WeatherDeterminate
from wps_shared.schemas.stations import WeatherStation
from wps_shared.weather_models import ModelEnum

from wps_weather_data.by_time import ByTimeTable
from wps_weather_data.morecast import fetch_model_predictions

RUN_TS = datetime(2026, 11, 12, 12, tzinfo=UTC)
AT_1800 = datetime(2026, 11, 12, 18, tzinfo=UTC)
AT_2000 = datetime(2026, 11, 12, 20, tzinfo=UTC)
START = datetime(2026, 11, 12, tzinfo=UTC)
END = datetime(2026, 11, 14, tzinfo=UTC)
STATIONS = [
    WeatherStation(code=322, name="AFTON", lat=50.6, long=-120.4),
    WeatherStation(code=209, name="ALEXIS CREEK", lat=52.1, long=-123.3),
]


def make_rows(times, temperature=10.0, station_codes=(322,)):
    return [
        {
            "station_code": code,
            "prediction_timestamp": time,
            "tmp_tgl_2": temperature,
            "rh_tgl_2": 50.0,
            "wind_tgl_10": 5.0,
            "wdir_tgl_10": 180.0,
            "bias_adjusted_temperature": temperature + 1,
            "bias_adjusted_rh": 51.0,
            "bias_adjusted_wind_speed": 6.0,
            "bias_adjusted_wdir": 181.0,
            "delta_precip": 0.5,
            "precip_24h": 4.0,
            "bias_adjusted_precip_24h": 4.5,
        }
        for code in station_codes
        for time in times
    ]


@pytest.fixture
def by_time(tmp_path):
    return ByTimeTable(str(tmp_path / "by_time"))


def test_no_table_gives_no_predictions(by_time):
    assert fetch_model_predictions(by_time, STATIONS, START, END) == []


def test_daily_row_becomes_model_and_bias_adjusted_values(by_time):
    by_time.merge_run(ModelEnum.GDPS, RUN_TS, make_rows([AT_1800, AT_2000]))

    model, bias = fetch_model_predictions(by_time, STATIONS, START, END)

    assert model.determinate == WeatherDeterminate.GDPS
    assert (model.station_code, model.station_name) == (322, "AFTON")
    assert model.utc_timestamp == AT_2000
    assert model.prediction_run_timestamp == RUN_TS
    assert (model.temperature, model.relative_humidity) == (10.0, 50.0)
    assert (model.wind_speed, model.wind_direction) == (5.0, 180.0)
    # The 24-hour precipitation, not the precipitation since the previous prediction.
    assert model.precipitation == 4.0

    assert bias.determinate == WeatherDeterminate.GDPS_BIAS
    assert bias.utc_timestamp == AT_2000
    assert (bias.temperature, bias.relative_humidity) == (11.0, 51.0)
    assert (bias.wind_speed, bias.wind_direction) == (6.0, 181.0)
    assert bias.precipitation == 4.5


def test_newest_run_is_the_one_returned(by_time):
    by_time.merge_run(ModelEnum.GDPS, RUN_TS, make_rows([AT_2000], temperature=10.0))
    newer = RUN_TS + timedelta(hours=12)
    by_time.merge_run(ModelEnum.GDPS, newer, make_rows([AT_2000], temperature=12.0))

    model, _ = fetch_model_predictions(by_time, STATIONS, START, END)

    assert model.temperature == 12.0
    assert model.prediction_run_timestamp == newer


def test_only_requested_stations_and_times(by_time):
    next_day = AT_2000 + timedelta(days=1)
    by_time.merge_run(
        ModelEnum.GDPS, RUN_TS, make_rows([AT_2000, next_day], station_codes=(322, 209, 1))
    )

    results = fetch_model_predictions(by_time, STATIONS[:1], START, AT_2000)

    assert {(r.station_code, r.utc_timestamp) for r in results} == {(322, AT_2000)}


def test_ecmwf_is_included(by_time):
    by_time.merge_run(ModelEnum.ECMWF, RUN_TS, make_rows([AT_2000]))
    by_time.merge_run(ModelEnum.HRDPS, RUN_TS, make_rows([AT_2000]))

    results = fetch_model_predictions(by_time, STATIONS, START, END)

    assert sorted(r.determinate for r in results) == sorted(
        [
            WeatherDeterminate.ECMWF,
            WeatherDeterminate.ECMWF_BIAS,
            WeatherDeterminate.HRDPS,
            WeatherDeterminate.HRDPS_BIAS,
        ]
    )
