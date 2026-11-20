from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from wps_shared.weather_models import ModelEnum

from wps_weather_data.addresser import StationWeatherAddresser
from wps_weather_data.by_station import STATION_ROWS_SCHEMA, ByStationTable, build
from wps_weather_data.by_time import ACTUALS, DAILY, HOURLY, ByTimeTable
from wps_weather_data.table import TABLE_CONFIGURATION
from wps_weather_data.wf1 import actuals_table, daily_actuals_table

FETCHED = datetime(2026, 11, 17, 21, tzinfo=UTC)


def noon(year, month=7, day=15):
    return datetime(year, month, day, 20, tzinfo=UTC)


def daily(time, station_code=322, temperature=20.0):
    return SimpleNamespace(
        code=station_code,
        for_datetime=time,
        temperature=temperature,
        relative_humidity=40.0,
        wind_speed=5.0,
        wind_direction=180.0,
        precipitation=1.5,
    )


def model_rows(times, station_code=322, temperature=18.0):
    return [
        {
            "station_code": station_code,
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
        for time in times
    ]


@pytest.fixture
def by_time(tmp_path):
    return ByTimeTable(str(tmp_path / "by_time"))


@pytest.fixture
def by_station(tmp_path):
    return ByStationTable(str(tmp_path / "by_station"))


def temperatures(rows):
    return [(row["timestamp"].year, row["temperature"]) for row in rows.to_pylist()]


def partitions(by_station):
    return sorted(
        {
            (row["resolution"], row["station_code"], row["year"])
            for row in by_station.dataset()
            .to_table(columns=["resolution", "station_code", "year"])
            .to_pylist()
        }
    )


def test_build_year_writes_each_stations_rows(by_time, by_station):
    by_time.merge_wf1_rows(
        daily_actuals_table(
            [daily(noon(2026)), daily(noon(2026), station_code=209), daily(noon(2025))], FETCHED
        )
    )

    assert by_station.build_year(by_time, DAILY, 2026) == 2

    assert partitions(by_station) == [(DAILY, 209, 2026), (DAILY, 322, 2026)]
    rows = by_station.read(DAILY, 322)
    assert rows.schema.equals(STATION_ROWS_SCHEMA)
    assert temperatures(rows) == [(2026, 20.0)]
    assert rows["source"].to_pylist() == [ACTUALS]
    assert rows["precipitation"].to_pylist() == [1.5]


def test_resolutions_are_kept_apart(by_time, by_station):
    by_time.merge_wf1_rows(daily_actuals_table([daily(noon(2026))], FETCHED))
    hour = SimpleNamespace(
        station_code=322,
        weather_date=noon(2026),
        temperature=21.0,
        relative_humidity=40.0,
        wind_speed=5.0,
        wind_direction=180.0,
        precipitation=0.1,
    )
    by_time.merge_wf1_rows(actuals_table([hour], FETCHED))

    assert build(by_station, by_time, 2026, 2026)

    assert temperatures(by_station.read(DAILY, 322)) == [(2026, 20.0)]
    assert temperatures(by_station.read(HOURLY, 322)) == [(2026, 21.0)]


def test_with_no_by_time_table_nothing_is_written(by_time, by_station):
    assert by_station.build_year(by_time, DAILY, 2026) == 0
    assert not by_station.exists()
    assert by_station.read(DAILY, 322).num_rows == 0


def test_a_year_with_no_rows_writes_nothing(by_time, by_station):
    by_time.merge_wf1_rows(daily_actuals_table([daily(noon(2025))], FETCHED))

    assert by_station.build_year(by_time, DAILY, 2026) == 0
    assert not by_station.exists()


def test_a_stations_record_spans_years_sorted_by_source_then_time(by_time, by_station):
    by_time.merge_wf1_rows(
        daily_actuals_table(
            [daily(noon(year), temperature=float(year - 2000)) for year in (2026, 2024, 2025)],
            FETCHED,
        )
    )
    by_time.merge_run(ModelEnum.GDPS, noon(2026) - timedelta(hours=8), model_rows([noon(2026)]))

    assert build(by_station, by_time, 2024, 2026, resolutions=[DAILY])

    rows = by_station.read(DAILY, 322)
    assert [(row["source"], row["timestamp"].year) for row in rows.to_pylist()] == [
        (ACTUALS, 2024),
        (ACTUALS, 2025),
        (ACTUALS, 2026),
        ("GDPS", 2026),
    ]
    assert partitions(by_station) == [(DAILY, 322, 2024), (DAILY, 322, 2025), (DAILY, 322, 2026)]


def test_read_can_be_limited_to_sources(by_time, by_station):
    by_time.merge_wf1_rows(daily_actuals_table([daily(noon(2026))], FETCHED))
    by_time.merge_run(ModelEnum.GDPS, noon(2026) - timedelta(hours=8), model_rows([noon(2026)]))
    by_station.build_year(by_time, DAILY, 2026)

    assert by_station.read(DAILY, 322)["source"].to_pylist() == [ACTUALS, "GDPS"]
    assert by_station.read(DAILY, 322, [ACTUALS])["source"].to_pylist() == [ACTUALS]


def test_the_nightly_run_replaces_only_the_current_year(by_time, by_station):
    by_time.merge_wf1_rows(daily_actuals_table([daily(noon(2025)), daily(noon(2026))], FETCHED))
    build(by_station, by_time, 2025, 2026)
    by_time.merge_wf1_rows(
        daily_actuals_table(
            [daily(noon(2025), temperature=1.0), daily(noon(2026), temperature=2.0)],
            FETCHED + timedelta(hours=1),
        )
    )

    build(by_station, by_time, 2026, 2026)

    # The correction to the year that has ended waits for a rebuild from that year.
    assert temperatures(by_station.read(DAILY, 322)) == [(2025, 20.0), (2026, 2.0)]

    build(by_station, by_time, 2025, 2026)

    assert temperatures(by_station.read(DAILY, 322)) == [(2025, 1.0), (2026, 2.0)]


def test_rebuilding_a_year_leaves_one_copy_of_it(by_time, by_station):
    by_time.merge_wf1_rows(daily_actuals_table([daily(noon(2026))], FETCHED))

    by_station.build_year(by_time, DAILY, 2026)
    by_station.build_year(by_time, DAILY, 2026)

    assert by_station.read(DAILY, 322).num_rows == 1
    assert by_station.dataset().count_rows() == 1


def test_rebuilding_a_year_leaves_other_years_and_resolutions_alone(by_time, by_station):
    by_time.merge_wf1_rows(daily_actuals_table([daily(noon(2025)), daily(noon(2026))], FETCHED))
    build(by_station, by_time, 2025, 2026, resolutions=[DAILY])
    before = by_station.open().version()

    by_station.build_year(by_time, DAILY, 2026)

    assert by_station.open().version() == before + 1
    assert temperatures(by_station.read(DAILY, 322)) == [(2025, 20.0), (2026, 20.0)]


def test_a_year_that_fails_does_not_stop_the_others(by_time, by_station, monkeypatch):
    by_time.merge_wf1_rows(daily_actuals_table([daily(noon(2025)), daily(noon(2026))], FETCHED))
    build_year = by_station.build_year

    def failing_2025(by_time, resolution, year):
        if year == 2025:
            raise OSError("object store is down")
        return build_year(by_time, resolution, year)

    monkeypatch.setattr(by_station, "build_year", failing_2025)

    assert build(by_station, by_time, 2025, 2026, resolutions=[DAILY]) is False
    assert temperatures(by_station.read(DAILY, 322)) == [(2026, 20.0)]


def test_dev_deployments_keep_their_own_table(monkeypatch):
    monkeypatch.setenv("SUFFIX", "pr-123")

    assert (
        StationWeatherAddresser().get_by_station_key() == "dev/pr-123/weather/stations/by_station"
    )


def test_several_stations_are_read_together(by_time, by_station):
    by_time.merge_wf1_rows(
        daily_actuals_table(
            [
                daily(noon(2025), station_code=322, temperature=1.0),
                daily(noon(2026), station_code=322, temperature=2.0),
                daily(noon(2026), station_code=209, temperature=3.0),
                daily(noon(2026), station_code=1, temperature=4.0),
            ],
            FETCHED,
        )
    )
    build(by_station, by_time, 2025, 2026, resolutions=[DAILY])

    rows = by_station.read_stations(DAILY, [322, 209, 999])

    assert [
        (row["station_code"], row["timestamp"].year, row["temperature"]) for row in rows.to_pylist()
    ] == [
        (209, 2026, 3.0),
        (322, 2025, 1.0),
        (322, 2026, 2.0),
    ]
    assert by_station.read_stations(DAILY, []).num_rows == 0


def test_read_can_be_limited_to_years(by_time, by_station):
    by_time.merge_wf1_rows(
        daily_actuals_table(
            [daily(noon(year), temperature=float(year - 2000)) for year in (2024, 2025, 2026)],
            FETCHED,
        )
    )
    build(by_station, by_time, 2024, 2026, resolutions=[DAILY])

    rows = by_station.read_stations(DAILY, [322], years=[2025, 2026])

    assert temperatures(rows) == [(2025, 25.0), (2026, 26.0)]


def test_tables_checkpoint_themselves(by_time, by_station):
    """by_time and by_station are created with a checkpoint interval, so a rebuild of many
    years leaves checkpoints rather than a long log for every reader to replay."""
    by_time.merge_wf1_rows(
        daily_actuals_table([daily(noon(year)) for year in range(2000, 2012)], noon(2026))
    )
    for year in range(2000, 2012):
        by_station.build_year(by_time, DAILY, year)

    for table in (by_time, by_station):
        delta_table = table.open()
        assert delta_table.metadata().configuration == TABLE_CONFIGURATION
    # 12 commits with an interval of 10: a checkpoint at version 9.
    log = Path(by_station.table_uri) / "_delta_log"
    assert (log / "00000000000000000009.checkpoint.parquet").exists()
