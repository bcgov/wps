from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from wps_shared.weather_models import ModelEnum

from wps_weather_data.by_time import ByTimeTable
from wps_weather_data.maintenance import maintain_all
from wps_weather_data.runs import RunsTable

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
