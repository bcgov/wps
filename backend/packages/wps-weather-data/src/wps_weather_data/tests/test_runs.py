from datetime import UTC, datetime, timedelta

import pyarrow as pa
import pytest
from wps_shared.weather_models import ModelEnum

from wps_weather_data.runs import RUNS_SCHEMA, RunsTable, build_run_table

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
def table(tmp_path):
    return RunsTable(str(tmp_path / "runs"))


def test_build_run_table_matches_schema_and_sorts():
    result = build_run_table(ModelEnum.GDPS, RUN_TS, make_rows([322, 101]), INGESTED_AT)

    assert result.schema == RUNS_SCHEMA
    assert result["station_code"].to_pylist() == [101, 101, 322, 322]
    assert result["prediction_timestamp"].to_pylist()[:2] == [RUN_TS, RUN_TS + timedelta(hours=3)]
    assert result["run_date"].to_pylist()[0] == RUN_TS.date()
    assert result["tmp_tgl_2"].type == pa.float32()
    # A value column the row does not have is null.
    assert result["rh_tgl_2"].null_count == 4


def test_append_then_read_round_trips(table):
    written = table.append_run(
        ModelEnum.GDPS, RUN_TS, make_rows([101, 322]), ingested_at=INGESTED_AT
    )

    result = table.read(ModelEnum.GDPS, RUN_TS, RUN_TS)

    assert written == 4
    assert result.schema == RUNS_SCHEMA
    assert result["station_code"].to_pylist() == [101, 101, 322, 322]
    assert result["tmp_tgl_2"].to_pylist() == [10.0, 13.0, 10.0, 13.0]
    assert set(result["ingested_at"].to_pylist()) == {INGESTED_AT}


def test_read_returns_newest_version_of_a_reprocessed_run(table):
    later = INGESTED_AT + timedelta(days=1)
    table.append_run(
        ModelEnum.GDPS,
        RUN_TS,
        make_rows([101, 322], temperature=10.0),
        ingested_at=INGESTED_AT,
    )
    # The reprocessed run no longer has station 322.
    table.append_run(
        ModelEnum.GDPS,
        RUN_TS,
        make_rows([101], temperature=20.0),
        ingested_at=later,
    )

    result = table.read(ModelEnum.GDPS, RUN_TS, RUN_TS)
    only_322 = table.read(ModelEnum.GDPS, RUN_TS, RUN_TS, station_codes=[322])

    assert result["station_code"].to_pylist() == [101, 101]
    assert result["tmp_tgl_2"].to_pylist() == [20.0, 23.0]
    assert set(result["ingested_at"].to_pylist()) == {later}
    # The older version's row for 322 must not come back when filtering to that station.
    assert only_322.num_rows == 0


def test_read_filters_by_model_run_range_and_station(table):
    next_run = RUN_TS + timedelta(hours=12)
    table.append_run(ModelEnum.GDPS, RUN_TS, make_rows([101, 322]), ingested_at=INGESTED_AT)
    table.append_run(ModelEnum.GDPS, next_run, make_rows([101]), ingested_at=INGESTED_AT)
    table.append_run(ModelEnum.RDPS, RUN_TS, make_rows([101]), ingested_at=INGESTED_AT)

    one_run = table.read(ModelEnum.GDPS, RUN_TS, RUN_TS)
    both_runs = table.read(ModelEnum.GDPS, RUN_TS, next_run)
    one_station = table.read(ModelEnum.GDPS, RUN_TS, next_run, station_codes=[322])

    assert one_run.num_rows == 4
    assert set(one_run["model"].to_pylist()) == {"GDPS"}
    assert both_runs.num_rows == 6
    assert set(one_station["station_code"].to_pylist()) == {322}
    assert one_station.num_rows == 2


def test_append_with_no_rows_writes_nothing(table):
    written = table.append_run(ModelEnum.GDPS, RUN_TS, [], ingested_at=INGESTED_AT)

    assert written == 0
    assert table.read(ModelEnum.GDPS, RUN_TS, RUN_TS).num_rows == 0


def test_read_before_table_exists_returns_empty(table):
    result = table.read(ModelEnum.GDPS, RUN_TS, RUN_TS)

    assert result.num_rows == 0
    assert result.schema == RUNS_SCHEMA


def test_a_reused_table_sees_runs_appended_after_its_first_read(table):
    next_run = RUN_TS + timedelta(hours=12)
    table.append_run(ModelEnum.GDPS, RUN_TS, make_rows([101]), ingested_at=INGESTED_AT)
    assert table.read(ModelEnum.GDPS, RUN_TS, next_run).num_rows == 2

    # Appended through another object, as another process would.
    RunsTable(table.table_uri).append_run(
        ModelEnum.GDPS, next_run, make_rows([101]), ingested_at=INGESTED_AT
    )

    assert table.read(ModelEnum.GDPS, RUN_TS, next_run).num_rows == 4


def test_a_reused_table_is_opened_once(table):
    table.append_run(ModelEnum.GDPS, RUN_TS, make_rows([101]), ingested_at=INGESTED_AT)

    first = table.open()
    second = table.open()

    assert first is second


def test_has_run_is_true_only_for_a_published_run(table):
    assert not table.has_run(ModelEnum.GDPS, RUN_TS)

    table.append_run(ModelEnum.GDPS, RUN_TS, make_rows([322]))

    assert table.has_run(ModelEnum.GDPS, RUN_TS)
    assert not table.has_run(ModelEnum.RDPS, RUN_TS)
    assert not table.has_run(ModelEnum.GDPS, RUN_TS + timedelta(hours=12))


def test_latest_run_ts_is_the_newest_run_since(table):
    since = RUN_TS - timedelta(days=1)
    assert table.latest_run_ts(ModelEnum.ECMWF, since) is None

    table.append_run(ModelEnum.ECMWF, RUN_TS, make_rows([322]))
    table.append_run(ModelEnum.ECMWF, RUN_TS - timedelta(hours=12), make_rows([322]))
    table.append_run(ModelEnum.GDPS, RUN_TS + timedelta(hours=12), make_rows([322]))

    assert table.latest_run_ts(ModelEnum.ECMWF, since) == RUN_TS
    assert table.latest_run_ts(ModelEnum.ECMWF, RUN_TS + timedelta(hours=1)) is None


def test_read_can_keep_a_prediction_range_and_some_columns(table):
    table.append_run(ModelEnum.GDPS, RUN_TS, make_rows([322], hours=(0, 3, 6)))

    result = table.read(
        ModelEnum.GDPS,
        RUN_TS,
        RUN_TS,
        predicted_from=RUN_TS + timedelta(hours=3),
        predicted_to=RUN_TS + timedelta(hours=6),
        columns=["prediction_timestamp", "tmp_tgl_2"],
    )

    assert result.column_names == ["prediction_timestamp", "tmp_tgl_2"]
    assert result["tmp_tgl_2"].to_pylist() == [13.0, 16.0]


def test_read_with_some_columns_before_table_exists_returns_empty(table):
    result = table.read(ModelEnum.GDPS, RUN_TS, RUN_TS, columns=["station_code"])

    assert result.num_rows == 0
    assert result.column_names == ["station_code"]
