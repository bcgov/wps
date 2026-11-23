from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from wps_shared.weather_models import ModelEnum

from wps_weather_data.by_time import ByTimeTable
from wps_weather_data.maintenance import maintain_all, maintain_grids
from wps_weather_data.runs import RunsTable
from wps_weather_data.tests.grid_helpers import RUN, fake_datamart, load_run, store, stored_bytes

RUN_TS = datetime(2026, 11, 12, 0, tzinfo=UTC)


def rows():
    return [{"station_code": 322, "prediction_timestamp": RUN_TS, "tmp_tgl_2": 10.0}]


@pytest.fixture
def runs(tmp_path):
    """A runs table holding four runs from one day, each in its own small file."""
    table = RunsTable(str(tmp_path / "runs"))
    for hour in (0, 6, 12, 18):
        table.append_run(ModelEnum.GDPS, RUN_TS + timedelta(hours=hour), rows())
    return table


def test_maintain_compacts_and_deletes_the_replaced_files(runs):
    result = runs.maintain(retention_hours=0, enforce_retention_duration=False)

    assert result == {"files_added": 1, "files_removed": 4, "files_deleted": 4}
    assert len(runs.open().file_uris()) == 1
    assert runs.read(ModelEnum.GDPS, RUN_TS, RUN_TS + timedelta(days=1)).num_rows == 4


def test_maintain_keeps_replaced_files_inside_the_retention_window(runs):
    result = runs.maintain()

    assert result == {"files_added": 1, "files_removed": 4, "files_deleted": 0}


def test_maintain_all_skips_tables_that_do_not_exist(runs, tmp_path):
    by_time = ByTimeTable(str(tmp_path / "by_time"))

    succeeded = maintain_all([runs, by_time])

    assert succeeded is True
    assert len(runs.open().file_uris()) == 1
    assert by_time.exists() is False


def test_maintain_all_reports_failure_but_still_maintains_the_other_tables():
    failing = MagicMock()
    failing.maintain.side_effect = OSError("object store is down")
    working = MagicMock()

    succeeded = maintain_all([failing, working])

    assert succeeded is False
    working.maintain.assert_called_once()


def test_main_maintains_runs_by_time_wf1_and_every_models_staging(monkeypatch):
    from wps_weather_data import maintenance
    from wps_weather_data.staging import StagingTable

    maintained = []
    monkeypatch.setattr(maintenance, "configure_logging", lambda: None)
    monkeypatch.setattr(
        maintenance, "maintain_all", lambda tables: maintained.extend(tables) or True
    )
    grid_stores = []
    monkeypatch.setattr(
        maintenance, "maintain_grids", lambda stores, now: grid_stores.extend(stores) or True
    )

    with pytest.raises(SystemExit) as exit_info:
        maintenance.main()

    assert exit_info.value.code == 0
    assert [(s.model.name, s.store) for s in grid_stores] == [
        (model, store) for model in ("HRDPS", "RDPS", "GDPS") for store in ("recent", "history")
    ]
    from wps_weather_data.wf1 import Wf1Table

    assert [type(table) for table in maintained[:3]] == [RunsTable, ByTimeTable, Wf1Table]
    staging_models = [table.model for table in maintained if isinstance(table, StagingTable)]
    assert staging_models == list(ModelEnum)


def test_grid_stores_reclaim_deleted_runs_and_skip_missing_ones(monkeypatch, tmp_path):
    fake_datamart(monkeypatch)
    recent, missing = store(tmp_path, "recent"), store(tmp_path, "history")
    for hours_ago in (12, 6, 0):
        crop, variables = load_run(tmp_path, RUN - timedelta(hours=hours_ago))
        recent.write_run(RUN - timedelta(hours=hours_ago), crop, variables.values())
    recent.delete_runs_before(RUN)
    size = stored_bytes(tmp_path)

    # Far enough ahead that the deleted runs' snapshots and objects are past their retention.
    assert maintain_grids([recent, missing], RUN + timedelta(days=30))

    assert stored_bytes(tmp_path) < size
    assert recent.run_times() == [RUN]
    assert not missing.exists()
