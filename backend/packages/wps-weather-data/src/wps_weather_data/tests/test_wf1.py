from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import math
import pytest

from wps_weather_data.by_time import ACTUALS, DAILY, FORECAST, HOURLY, ByTimeTable
from wps_weather_data.wf1 import (
    Wf1Table,
    actuals_table,
    daily_actuals_table,
    forecasts_table,
)

AT_1900 = datetime(2026, 11, 17, 19, tzinfo=UTC)
NOON = datetime(2026, 11, 18, 20, tzinfo=UTC)
FETCHED = datetime(2026, 11, 17, 20, 15, tzinfo=UTC)


def record(time, station_code=322, temperature=10.0, created_at=None, **values):
    fields = {
        "relative_humidity": 60.0,
        "wind_speed": 5.0,
        "wind_direction": 180.0,
        "precipitation": 0.2,
    }
    fields.update(values)
    return SimpleNamespace(
        station_code=station_code,
        weather_date=time,
        temperature=temperature,
        created_at=created_at,
        **fields,
    )


@pytest.fixture
def wf1(tmp_path):
    return Wf1Table(str(tmp_path / "wf1"))


@pytest.fixture
def by_time(tmp_path):
    return ByTimeTable(str(tmp_path / "by_time"))


def test_actuals_are_hourly_rows():
    rows = actuals_table([record(AT_1900.isoformat())], FETCHED).to_pylist()

    assert rows == [
        {
            "resolution": HOURLY,
            "source": ACTUALS,
            "month": "2026-11",
            "station_code": 322,
            "timestamp": AT_1900,
            "temperature": 10.0,
            "relative_humidity": 60.0,
            "wind_speed": 5.0,
            "wind_direction": 180.0,
            "precipitation": pytest.approx(0.2),
            "bias_adjusted_temperature": None,
            "bias_adjusted_relative_humidity": None,
            "bias_adjusted_wind_speed": None,
            "bias_adjusted_wind_direction": None,
            "bias_adjusted_precipitation": None,
            "run_ts": None,
            "ingested_at": FETCHED,
        }
    ]


def test_forecasts_are_daily_rows():
    row = forecasts_table([record(NOON)], FETCHED).to_pylist()[0]

    assert (row["resolution"], row["source"], row["timestamp"]) == (DAILY, FORECAST, NOON)


@pytest.mark.parametrize(
    "values",
    [
        {"relative_humidity": 101.0},
        {"relative_humidity": None},
        {"wind_speed": -1.0},
        {"wind_direction": 361.0},
        {"precipitation": math.nan},
    ],
)
def test_a_missing_or_out_of_range_value_is_null(values):
    row = actuals_table([record(AT_1900, **values)], FETCHED).to_pylist()[0]

    (column,) = values
    assert row[column] is None
    assert row["temperature"] == 10.0


def test_history_keeps_each_records_fetch_time():
    created_at = datetime(2026, 11, 17, 19, 15, tzinfo=UTC)

    row = actuals_table([record(AT_1900, created_at=created_at)]).to_pylist()[0]

    assert row["ingested_at"] == created_at


def test_append_changed_appends_new_rows(wf1):
    appended = wf1.append_changed(actuals_table([record(AT_1900)], FETCHED))

    assert appended.num_rows == 1
    assert wf1.dataset().count_rows() == 1


def test_append_changed_skips_an_unchanged_row(wf1):
    wf1.append_changed(actuals_table([record(AT_1900)], FETCHED))

    appended = wf1.append_changed(actuals_table([record(AT_1900)], FETCHED + timedelta(hours=1)))

    assert appended.num_rows == 0
    assert wf1.dataset().count_rows() == 1


def test_append_changed_keeps_a_correction_as_a_second_version(wf1):
    wf1.append_changed(actuals_table([record(AT_1900, temperature=10.0)], FETCHED))

    wf1.append_changed(
        actuals_table([record(AT_1900, temperature=11.0)], FETCHED + timedelta(hours=1))
    )

    assert sorted(wf1.dataset().to_table()["temperature"].to_pylist()) == [10.0, 11.0]


def test_append_changed_compares_versions_in_one_batch_in_fetch_order(wf1):
    first = datetime(2026, 11, 17, 8, tzinfo=UTC)
    versions = [
        record(NOON, temperature=13.0, created_at=first + timedelta(hours=2)),
        record(NOON, temperature=15.0, created_at=first),
        record(NOON, temperature=15.0, created_at=first + timedelta(hours=1)),
    ]

    appended = wf1.append_changed(forecasts_table(versions))

    assert appended["temperature"].to_pylist() == [15.0, 13.0]


def test_merge_wf1_rows_takes_the_newest_version(by_time):
    first = datetime(2026, 11, 17, 8, tzinfo=UTC)
    versions = [
        record(NOON, temperature=15.0, created_at=first),
        record(NOON, temperature=13.0, created_at=first + timedelta(hours=1)),
    ]

    assert by_time.merge_wf1_rows(forecasts_table(versions)) == 1

    rows = by_time.read(DAILY, [FORECAST], NOON, NOON).to_pylist()
    assert [row["temperature"] for row in rows] == [13.0]


def test_merge_wf1_rows_does_not_undo_a_newer_fetch(by_time):
    newer = actuals_table([record(AT_1900, temperature=12.0)], FETCHED + timedelta(hours=1))
    older = actuals_table([record(AT_1900, temperature=10.0)], FETCHED)

    by_time.merge_wf1_rows(newer)
    by_time.merge_wf1_rows(older)

    rows = by_time.read(HOURLY, [ACTUALS], AT_1900, AT_1900).to_pylist()
    assert [row["temperature"] for row in rows] == [12.0]


def test_merge_wf1_rows_with_no_rows_writes_nothing(by_time):
    assert by_time.merge_wf1_rows(actuals_table([], FETCHED)) == 0
    assert not by_time.exists()


def test_daily_actuals_are_daily_rows_with_wf1s_precip_total():
    daily = SimpleNamespace(
        code=322,
        for_datetime=NOON,
        temperature=12.0,
        relative_humidity=60.0,
        wind_speed=5.0,
        wind_direction=180.0,
        precipitation=4.8,
    )

    (row,) = daily_actuals_table([daily], FETCHED).to_pylist()

    assert (row["resolution"], row["source"], row["month"]) == (DAILY, ACTUALS, "2026-11")
    assert (row["station_code"], row["timestamp"]) == (322, NOON)
    assert row["temperature"] == 12.0
    assert row["precipitation"] == pytest.approx(4.8)
    assert row["ingested_at"] == FETCHED
