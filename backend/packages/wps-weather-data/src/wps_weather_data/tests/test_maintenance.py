from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from deltalake import DeltaTable
from wps_shared.weather_models import ModelEnum

from wps_weather_data import maintenance
from wps_weather_data.runs import append_run, read_runs

RUN_TS = datetime(2026, 11, 12, 0, tzinfo=UTC)


def rows():
    return [{"station_code": 322, "prediction_timestamp": RUN_TS, "tmp_tgl_2": 10.0}]


@pytest.fixture
def runs_uri(tmp_path):
    """A runs table holding four runs from one day, each in its own small file."""
    uri = str(tmp_path / "runs")
    for hour in (0, 6, 12, 18):
        append_run(ModelEnum.GDPS, RUN_TS + timedelta(hours=hour), rows(), table_uri=uri)
    return uri


def test_maintain_table_compacts_and_deletes_the_replaced_files(runs_uri):
    result = maintenance.maintain_table(
        runs_uri, retention_hours=0, enforce_retention_duration=False
    )

    table = DeltaTable(runs_uri)
    assert result == {"files_added": 1, "files_removed": 4, "files_deleted": 4}
    assert len(table.file_uris()) == 1
    assert (
        read_runs(ModelEnum.GDPS, RUN_TS, RUN_TS + timedelta(days=1), table_uri=runs_uri).num_rows
        == 4
    )


def test_maintain_table_keeps_replaced_files_inside_the_retention_window(runs_uri):
    result = maintenance.maintain_table(runs_uri)

    assert result == {"files_added": 1, "files_removed": 4, "files_deleted": 0}


def resolve_under(directory):
    return lambda key, table_uri, storage_options: (str(directory / key.split("/")[-1]), None)


def test_maintain_all_skips_tables_that_do_not_exist(runs_uri, tmp_path):
    with (
        patch.object(maintenance, "resolve_table", resolve_under(tmp_path)),
        patch.object(maintenance, "maintain_table", wraps=maintenance.maintain_table) as maintain,
    ):
        succeeded = maintenance.maintain_all()

    # runs exists, by_time does not.
    assert succeeded is True
    maintain.assert_called_once_with(runs_uri, None)


def test_maintain_all_reports_failure_but_still_maintains_the_other_tables(runs_uri, tmp_path):
    with (
        patch.object(maintenance, "resolve_table", resolve_under(tmp_path)),
        patch.object(maintenance.DeltaTable, "is_deltatable", return_value=True),
        patch.object(
            maintenance, "maintain_table", side_effect=[OSError("object store is down"), {}]
        ) as maintain,
    ):
        succeeded = maintenance.maintain_all()

    assert succeeded is False
    assert maintain.call_count == 2
