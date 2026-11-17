from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from wps_weather_data.actuals import (
    Observation,
    ObservedDailyPrecip,
    StationObservations,
    get_accumulated_precipitation,
)
from wps_weather_data.by_time import ByTimeTable
from wps_weather_data.wf1 import actuals_table

NOON = datetime(2026, 11, 17, 20, tzinfo=UTC)
FETCHED = datetime(2026, 11, 18, tzinfo=UTC)


def hour(offset: int, *, precipitation=1.0, temperature=10.0, relative_humidity=50.0):
    return Observation(
        NOON + timedelta(hours=offset), temperature, relative_humidity, 5.0, 180.0, precipitation
    )


def observations(*hours):
    return StationObservations({322: list(hours)})


def test_read_gives_each_stations_observations_in_time_order(tmp_path):
    by_time = ByTimeTable(str(tmp_path / "by_time"))
    records = [
        SimpleNamespace(
            station_code=code,
            weather_date=NOON + timedelta(hours=offset),
            temperature=float(offset),
            relative_humidity=50.0,
            wind_speed=5.0,
            wind_direction=180.0,
            precipitation=0.5,
        )
        for code in (322, 209)
        for offset in (1, 0)
    ]
    by_time.merge_wf1_rows(actuals_table(records, FETCHED))

    read = StationObservations.read(by_time, NOON, NOON + timedelta(hours=1))

    assert [o.temperature for o in read.hourly(322, NOON, NOON + timedelta(hours=1))] == [0.0, 1.0]
    assert read.accumulated_precip(209, NOON - timedelta(hours=1), NOON) == pytest.approx(0.5)


def test_no_table_gives_no_observations(tmp_path):
    read = StationObservations.read(ByTimeTable(str(tmp_path / "by_time")), NOON, NOON)

    assert read.hourly(322, NOON, NOON) == []


def test_hourly_needs_a_temperature_and_an_rh():
    kept = hour(0)
    observed = observations(kept, hour(1, temperature=None), hour(2, relative_humidity=None))

    assert observed.hourly(322, NOON, NOON + timedelta(hours=2)) == [kept]
    assert observed.hourly(209, NOON, NOON + timedelta(hours=2)) == []


def test_accumulated_precip_excludes_the_start_and_includes_the_end():
    observed = observations(
        hour(0, precipitation=1.0), hour(1, precipitation=2.0), hour(2, precipitation=4.0)
    )

    assert observed.accumulated_precip(322, NOON, NOON + timedelta(hours=2)) == 6.0
    assert get_accumulated_precipitation(observed, 322, NOON, NOON + timedelta(hours=1)) == 2.0


def test_accumulated_precip_skips_hours_with_no_precip_and_is_zero_with_none():
    observed = observations(hour(1, precipitation=None), hour(2, precipitation=4.0))

    assert observed.accumulated_precip(322, NOON, NOON + timedelta(hours=2)) == 4.0
    assert observed.accumulated_precip(209, NOON, NOON + timedelta(hours=2)) == 0


def test_precip_by_24h_sums_each_day_ending_at_the_day():
    next_noon = NOON + timedelta(hours=24)
    observed = observations(
        hour(0, precipitation=1.0),
        hour(1, precipitation=2.0),
        hour(24, precipitation=3.0),
    )

    assert observed.precip_by_24h(322, NOON, next_noon) == [
        ObservedDailyPrecip(NOON, 1.0),
        ObservedDailyPrecip(next_noon, 5.0),
    ]


def test_precip_by_24h_leaves_out_days_with_no_observations():
    observed = observations(hour(24, precipitation=3.0))

    assert observed.precip_by_24h(322, NOON, NOON + timedelta(hours=48)) == [
        ObservedDailyPrecip(NOON + timedelta(hours=24), 3.0)
    ]


def test_precip_by_24h_has_no_total_for_a_day_with_an_hour_missing_precip():
    observed = observations(hour(1, precipitation=None), hour(2, precipitation=3.0))

    assert observed.precip_by_24h(322, NOON + timedelta(hours=24), NOON + timedelta(hours=24)) == [
        ObservedDailyPrecip(NOON + timedelta(hours=24), None)
    ]
