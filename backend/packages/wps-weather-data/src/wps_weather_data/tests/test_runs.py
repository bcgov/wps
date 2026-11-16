from datetime import UTC, datetime, timedelta

import pyarrow as pa
import pytest

from wps_weather_data.runs import RUNS_SCHEMA, append_run, build_run_table, read_runs
from wps_shared.weather_models import ModelEnum

RUN_TS = datetime(2026, 11, 12, 12, tzinfo=UTC)
INGESTED_AT = datetime(2026, 11, 12, 16, tzinfo=UTC)


def make_rows(station_codes, temperature=10.0, hours=(0, 3)):
    return [
        {
            "station_code": code,
            "prediction_timestamp": RUN_TS + timedelta(hours=hour),
            "tmp_tgl_2": temperature + hour,
            "is_interpolated": False,
        }
        for code in station_codes
        for hour in hours
    ]


@pytest.fixture
def table_uri(tmp_path):
    return str(tmp_path / "runs")


def test_build_run_table_matches_schema_and_sorts():
    table = build_run_table(ModelEnum.GDPS, RUN_TS, make_rows([322, 101]), INGESTED_AT)

    assert table.schema == RUNS_SCHEMA
    assert table["station_code"].to_pylist() == [101, 101, 322, 322]
    assert table["prediction_timestamp"].to_pylist()[:2] == [RUN_TS, RUN_TS + timedelta(hours=3)]
    assert table["run_date"].to_pylist()[0] == RUN_TS.date()
    assert table["tmp_tgl_2"].type == pa.float32()
    # A value column the row does not have is null.
    assert table["rh_tgl_2"].null_count == 4


def test_append_then_read_round_trips(table_uri):
    written = append_run(
        ModelEnum.GDPS, RUN_TS, make_rows([101, 322]), ingested_at=INGESTED_AT, table_uri=table_uri
    )

    table = read_runs(ModelEnum.GDPS, RUN_TS, RUN_TS, table_uri=table_uri)

    assert written == 4
    assert table.schema == RUNS_SCHEMA
    assert table["station_code"].to_pylist() == [101, 101, 322, 322]
    assert table["tmp_tgl_2"].to_pylist() == [10.0, 13.0, 10.0, 13.0]
    assert set(table["ingested_at"].to_pylist()) == {INGESTED_AT}


def test_read_returns_newest_version_of_a_reprocessed_run(table_uri):
    later = INGESTED_AT + timedelta(days=1)
    append_run(
        ModelEnum.GDPS,
        RUN_TS,
        make_rows([101, 322], temperature=10.0),
        ingested_at=INGESTED_AT,
        table_uri=table_uri,
    )
    # The reprocessed run no longer has station 322.
    append_run(
        ModelEnum.GDPS,
        RUN_TS,
        make_rows([101], temperature=20.0),
        ingested_at=later,
        table_uri=table_uri,
    )

    table = read_runs(ModelEnum.GDPS, RUN_TS, RUN_TS, table_uri=table_uri)
    only_322 = read_runs(ModelEnum.GDPS, RUN_TS, RUN_TS, station_codes=[322], table_uri=table_uri)

    assert table["station_code"].to_pylist() == [101, 101]
    assert table["tmp_tgl_2"].to_pylist() == [20.0, 23.0]
    assert set(table["ingested_at"].to_pylist()) == {later}
    # The older version's row for 322 must not come back when filtering to that station.
    assert only_322.num_rows == 0


def test_read_filters_by_model_run_range_and_station(table_uri):
    next_run = RUN_TS + timedelta(hours=12)
    append_run(
        ModelEnum.GDPS, RUN_TS, make_rows([101, 322]), ingested_at=INGESTED_AT, table_uri=table_uri
    )
    append_run(
        ModelEnum.GDPS, next_run, make_rows([101]), ingested_at=INGESTED_AT, table_uri=table_uri
    )
    append_run(
        ModelEnum.RDPS, RUN_TS, make_rows([101]), ingested_at=INGESTED_AT, table_uri=table_uri
    )

    one_run = read_runs(ModelEnum.GDPS, RUN_TS, RUN_TS, table_uri=table_uri)
    both_runs = read_runs(ModelEnum.GDPS, RUN_TS, next_run, table_uri=table_uri)
    one_station = read_runs(
        ModelEnum.GDPS, RUN_TS, next_run, station_codes=[322], table_uri=table_uri
    )

    assert one_run.num_rows == 4
    assert set(one_run["model"].to_pylist()) == {"GDPS"}
    assert both_runs.num_rows == 6
    assert set(one_station["station_code"].to_pylist()) == {322}
    assert one_station.num_rows == 2


def test_append_with_no_rows_writes_nothing(table_uri):
    written = append_run(ModelEnum.GDPS, RUN_TS, [], ingested_at=INGESTED_AT, table_uri=table_uri)

    assert written == 0
    assert read_runs(ModelEnum.GDPS, RUN_TS, RUN_TS, table_uri=table_uri).num_rows == 0


def test_read_before_table_exists_returns_empty(table_uri):
    table = read_runs(ModelEnum.GDPS, RUN_TS, RUN_TS, table_uri=table_uri)

    assert table.num_rows == 0
    assert table.schema == RUNS_SCHEMA
