from datetime import UTC, datetime

import pytest
from wps_shared.weather_models import ModelEnum

from wps_weather_data.staging import StagedFile, StagingTable, run_partition

RUN_TS = datetime(2026, 11, 17, 0, tzinfo=UTC)
OTHER_RUN_TS = datetime(2026, 11, 17, 12, tzinfo=UTC)
AT_0300 = datetime(2026, 11, 17, 3, tzinfo=UTC)
AT_0600 = datetime(2026, 11, 17, 6, tzinfo=UTC)


@pytest.fixture
def staging(tmp_path):
    return StagingTable(ModelEnum.GDPS, str(tmp_path / "staging"))


def temperature_file(time, values, source=None):
    return StagedFile(
        source or f"tmp-{time:%H}",
        time,
        [(station_code, time, "tmp_tgl_2", value) for station_code, value in values.items()],
    )


def test_run_partition_is_the_run_in_utc():
    assert run_partition(RUN_TS) == "20261117T00"


def test_empty_table_has_nothing(staging):
    assert not staging.has_run(RUN_TS)
    assert staging.processed_sources(RUN_TS) == set()
    assert staging.station_values(RUN_TS) == {}
    staging.delete_run(RUN_TS)


def test_appending_no_files_writes_nothing(staging):
    assert staging.append_files(RUN_TS, []) == 0
    assert not staging.exists()


def test_processed_sources_are_the_files_staged_for_the_run(staging):
    staging.append_files(RUN_TS, [temperature_file(AT_0300, {322: 1.0}, source="a")])
    staging.append_files(RUN_TS, [temperature_file(AT_0600, {322: 2.0}, source="b")])
    staging.append_files(OTHER_RUN_TS, [temperature_file(AT_0600, {322: 3.0}, source="c")])

    assert staging.has_run(RUN_TS)
    assert staging.processed_sources(RUN_TS) == {"a", "b"}
    assert staging.processed_sources(OTHER_RUN_TS) == {"c"}


def test_last_written_at_is_when_the_run_was_last_staged(staging):
    assert staging.last_written_at(RUN_TS) is None
    staging.append_files(RUN_TS, [temperature_file(AT_0300, {322: 1.0}, source="a")])
    first = staging.last_written_at(RUN_TS)
    staging.append_files(RUN_TS, [temperature_file(AT_0600, {322: 2.0}, source="b")])

    assert staging.last_written_at(RUN_TS) > first
    assert staging.last_written_at(OTHER_RUN_TS) is None


def test_a_file_with_no_station_values_still_counts_as_processed(staging):
    staging.append_files(RUN_TS, [StagedFile("empty", AT_0300, [])])

    assert staging.processed_sources(RUN_TS) == {"empty"}
    assert staging.station_values(RUN_TS) == {}


def test_station_values_are_per_station_in_time_order(staging):
    staging.append_files(
        RUN_TS,
        [
            temperature_file(AT_0600, {322: 2.0, 209: 5.0}),
            temperature_file(AT_0300, {322: 1.0}),
            StagedFile(
                "rh-03",
                AT_0300,
                [(322, AT_0300, "rh_tgl_2", 50.0), (322, AT_0300, "not_a_model_field", 9.0)],
            ),
        ],
    )

    values = staging.station_values(RUN_TS)

    assert set(values) == {322, 209}
    assert [v["prediction_timestamp"] for v in values[322]] == [AT_0300, AT_0600]
    assert values[322][0] == {
        "prediction_timestamp": AT_0300,
        "tmp_tgl_2": 1.0,
        "rh_tgl_2": 50.0,
        "apcp_sfc_0": None,
        "wdir_tgl_10": None,
        "wind_tgl_10": None,
    }
    assert values[209] == [
        {
            "prediction_timestamp": AT_0600,
            "tmp_tgl_2": 5.0,
            "rh_tgl_2": None,
            "apcp_sfc_0": None,
            "wdir_tgl_10": None,
            "wind_tgl_10": None,
        }
    ]


def test_a_missing_value_stays_missing(staging):
    staging.append_files(RUN_TS, [temperature_file(AT_0300, {322: None})])

    assert staging.station_values(RUN_TS)[322][0]["tmp_tgl_2"] is None


def test_a_value_staged_again_takes_the_newest(staging):
    staging.append_files(RUN_TS, [temperature_file(AT_0300, {322: 1.0})])
    staging.append_files(RUN_TS, [temperature_file(AT_0300, {322: 7.0})])

    assert staging.station_values(RUN_TS)[322][0]["tmp_tgl_2"] == 7.0


def test_delete_run_removes_only_that_run(staging):
    staging.append_files(RUN_TS, [temperature_file(AT_0300, {322: 1.0}, source="a")])
    staging.append_files(OTHER_RUN_TS, [temperature_file(AT_0600, {322: 2.0}, source="b")])

    staging.delete_run(RUN_TS)

    assert not staging.has_run(RUN_TS)
    assert staging.processed_sources(RUN_TS) == set()
    assert staging.processed_sources(OTHER_RUN_TS) == {"b"}
