from datetime import UTC, datetime, timedelta

import pytest
from wps_shared.weather_models import ModelEnum

from wps_weather_data.by_time import (
    BY_TIME_SCHEMA,
    DAILY,
    HOURLY,
    OBSERVED_COLUMNS,
    ByTimeTable,
    _months,
    by_time_rows_from_run,
)
from wps_weather_data.runs import build_run_table

RUN_TS = datetime(2026, 11, 12, 12, tzinfo=UTC)
NEXT_RUN_TS = RUN_TS + timedelta(hours=12)
INGESTED_AT = datetime(2026, 11, 12, 16, tzinfo=UTC)
AT_1800 = datetime(2026, 11, 12, 18, tzinfo=UTC)
AT_2000 = datetime(2026, 11, 12, 20, tzinfo=UTC)
NEXT_DAY_2000 = AT_2000 + timedelta(days=1)
WINDOW = (RUN_TS, RUN_TS + timedelta(days=30))


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
def table(tmp_path):
    return ByTimeTable(str(tmp_path / "by_time"))


def test_every_prediction_is_hourly_and_only_2000_utc_is_daily():
    run = build_run_table(ModelEnum.GDPS, RUN_TS, make_rows([AT_1800, AT_2000]), INGESTED_AT)

    rows = by_time_rows_from_run(run)
    hourly = [row for row in rows.to_pylist() if row["resolution"] == HOURLY]
    daily = [row for row in rows.to_pylist() if row["resolution"] == DAILY]

    assert rows.schema == BY_TIME_SCHEMA
    assert [row["timestamp"] for row in hourly] == [AT_1800, AT_2000]
    assert [row["timestamp"] for row in daily] == [AT_2000]


def test_columns_are_mapped_from_the_run():
    run = build_run_table(ModelEnum.GDPS, RUN_TS, make_rows([AT_2000]), INGESTED_AT)

    hourly, daily = by_time_rows_from_run(run).to_pylist()

    assert daily == {
        "resolution": DAILY,
        "source": "GDPS",
        "month": "2026-11",
        "station_code": 322,
        "timestamp": AT_2000,
        "temperature": 10.0,
        "relative_humidity": 50.0,
        "wind_speed": 5.0,
        "wind_direction": 180.0,
        "precipitation": 4.0,
        "bias_adjusted_temperature": 11.0,
        "bias_adjusted_relative_humidity": 51.0,
        "bias_adjusted_wind_speed": 6.0,
        "bias_adjusted_wind_direction": 181.0,
        "bias_adjusted_precipitation": 4.5,
        **dict.fromkeys(OBSERVED_COLUMNS),
        "run_ts": RUN_TS,
        "ingested_at": INGESTED_AT,
    }
    # Hourly precipitation is the change since the previous prediction, with no bias adjustment.
    assert hourly["precipitation"] == 0.5
    assert hourly["bias_adjusted_precipitation"] is None


def test_merge_then_read_round_trips(table):
    offered = table.merge_run(
        ModelEnum.GDPS,
        RUN_TS,
        make_rows([AT_1800, AT_2000]),
        ingested_at=INGESTED_AT,
    )

    hourly = table.read(HOURLY, ["GDPS"], *WINDOW)
    daily = table.read(DAILY, ["GDPS"], *WINDOW)

    assert offered == 3
    assert hourly.schema == BY_TIME_SCHEMA
    assert hourly["timestamp"].to_pylist() == [AT_1800, AT_2000]
    assert daily["timestamp"].to_pylist() == [AT_2000]


def test_newer_run_replaces_the_times_it_predicts_and_keeps_the_rest(table):
    table.merge_run(
        ModelEnum.GDPS,
        RUN_TS,
        make_rows([AT_1800, AT_2000], temperature=10.0),
        ingested_at=INGESTED_AT,
    )
    # The next run starts after 18:00, so it no longer predicts it.
    table.merge_run(
        ModelEnum.GDPS,
        NEXT_RUN_TS,
        make_rows([AT_2000, NEXT_DAY_2000], temperature=20.0),
        ingested_at=INGESTED_AT,
    )

    hourly = table.read(HOURLY, ["GDPS"], *WINDOW).to_pylist()

    assert [(row["timestamp"], row["temperature"], row["run_ts"]) for row in hourly] == [
        (AT_1800, 10.0, RUN_TS),
        (AT_2000, 20.0, NEXT_RUN_TS),
        (NEXT_DAY_2000, 20.0, NEXT_RUN_TS),
    ]


def test_older_run_merged_later_fills_gaps_without_replacing_newer_rows(table):
    table.merge_run(
        ModelEnum.GDPS,
        NEXT_RUN_TS,
        make_rows([AT_2000], temperature=20.0),
        ingested_at=INGESTED_AT,
    )
    table.merge_run(
        ModelEnum.GDPS,
        RUN_TS,
        make_rows([AT_1800, AT_2000], temperature=10.0),
        ingested_at=INGESTED_AT,
    )

    hourly = table.read(HOURLY, ["GDPS"], *WINDOW).to_pylist()

    assert [(row["timestamp"], row["temperature"]) for row in hourly] == [
        (AT_1800, 10.0),
        (AT_2000, 20.0),
    ]


def test_merging_the_same_run_twice_does_not_duplicate_rows(table):
    for _ in range(2):
        table.merge_run(
            ModelEnum.GDPS,
            RUN_TS,
            make_rows([AT_1800, AT_2000]),
            ingested_at=INGESTED_AT,
        )

    assert table.read(HOURLY, ["GDPS"], *WINDOW).num_rows == 2
    assert table.read(DAILY, ["GDPS"], *WINDOW).num_rows == 1


def test_sources_and_stations_are_kept_apart(table):
    table.merge_run(
        ModelEnum.GDPS,
        RUN_TS,
        make_rows([AT_2000], temperature=10.0, station_codes=(101, 322)),
        ingested_at=INGESTED_AT,
    )
    table.merge_run(
        ModelEnum.RDPS,
        RUN_TS,
        make_rows([AT_2000], temperature=30.0),
        ingested_at=INGESTED_AT,
    )

    gdps = table.read(DAILY, ["GDPS"], *WINDOW)
    both = table.read(DAILY, ["GDPS", "RDPS"], *WINDOW)
    one_station = table.read(DAILY, ["GDPS"], *WINDOW, station_codes=[101])

    assert gdps["temperature"].to_pylist() == [10.0, 10.0]
    assert both.num_rows == 3
    assert one_station["station_code"].to_pylist() == [101]


def test_read_is_limited_to_the_time_range(table):
    table.merge_run(
        ModelEnum.GDPS,
        RUN_TS,
        make_rows([AT_2000, NEXT_DAY_2000]),
        ingested_at=INGESTED_AT,
    )

    rows = table.read(DAILY, ["GDPS"], AT_1800, AT_2000)

    assert rows["timestamp"].to_pylist() == [AT_2000]


def test_merge_with_no_rows_writes_nothing(table):
    offered = table.merge_run(ModelEnum.GDPS, RUN_TS, [], ingested_at=INGESTED_AT)

    assert offered == 0
    assert table.read(DAILY, ["GDPS"], *WINDOW).num_rows == 0


def test_months_cover_the_range_across_a_year_end():
    start = datetime(2025, 11, 30, tzinfo=UTC)
    end = datetime(2026, 2, 1, tzinfo=UTC)
    assert _months(start, end) == ["2025-11", "2025-12", "2026-01", "2026-02"]
    assert _months(end, end) == ["2026-02"]
