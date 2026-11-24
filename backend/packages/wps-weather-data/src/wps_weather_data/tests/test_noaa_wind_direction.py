from datetime import UTC, datetime, timedelta

import pytest
from wps_shared.weather_models import ModelEnum

from wps_weather_data.by_time import HOURLY, ByTimeTable
from wps_weather_data.noaa_wind_direction import (
    corrected_direction,
    corrected_rows,
    correct_stored_runs,
)
from wps_weather_data.runs import RunsTable

RUN = datetime(2026, 11, 20, 12, tzinfo=UTC)
TIME = RUN + timedelta(hours=6)
STORED = datetime(2026, 11, 20, 18, tzinfo=UTC)
DEPLOYED = datetime(2026, 11, 21, tzinfo=UTC)


@pytest.fixture
def tables(tmp_path):
    return RunsTable(str(tmp_path / "runs")), ByTimeTable(str(tmp_path / "by_time"))


def row(direction):
    return {
        "station_code": 322,
        "prediction_timestamp": TIME,
        "tmp_tgl_2": 5.0,
        "wdir_tgl_10": direction,
        "bias_adjusted_wdir": 200.0,
        "is_interpolated": False,
    }


def store(tables, run_ts, direction, ingested_at, model=ModelEnum.GFS):
    runs, by_time = tables
    runs.append_run(model, run_ts, [row(direction)], ingested_at=ingested_at)
    by_time.merge_run(model, run_ts, [row(direction)], ingested_at=ingested_at)


def directions(tables, model=ModelEnum.GFS):
    runs, by_time = tables
    stored = runs.read(model, RUN - timedelta(days=9), RUN + timedelta(days=9)).to_pylist()
    newest = by_time.read(HOURLY, [model.value], TIME, TIME).to_pylist()
    return [r["wdir_tgl_10"] for r in stored], [r["wind_direction"] for r in newest]


@pytest.mark.parametrize(
    "stored, right", [(90, 360), (360, 90), (270, 180), (180, 270), (45, 45), (308, 142)]
)
def test_a_mirrored_direction_is_corrected(stored, right):
    assert corrected_direction(stored) == right


def test_a_missing_direction_stays_missing():
    assert corrected_direction(None) is None


def test_only_the_models_that_were_mirrored_are_corrected():
    assert corrected_rows(ModelEnum.GFS, [row(90.0)])[0]["wdir_tgl_10"] == 360.0
    assert corrected_rows(ModelEnum.GDPS, [row(90.0)]) == [row(90.0)]


def test_stored_runs_are_corrected_once(tables):
    store(tables, RUN, 90.0, STORED)

    assert correct_stored_runs(*tables, ModelEnum.GFS, DEPLOYED, dry_run=False) == [RUN]
    assert directions(tables) == ([360.0], [360.0])
    assert correct_stored_runs(*tables, ModelEnum.GFS, DEPLOYED, dry_run=False) == []
    assert directions(tables) == ([360.0], [360.0])


def test_the_rest_of_a_corrected_run_is_unchanged(tables):
    store(tables, RUN, 90.0, STORED)
    correct_stored_runs(*tables, ModelEnum.GFS, DEPLOYED, dry_run=False)

    [corrected] = tables[0].read(ModelEnum.GFS, RUN, RUN).to_pylist()
    expected = row(360.0)
    assert {key: corrected[key] for key in expected} == expected


def test_runs_stored_since_the_fix_are_left_alone(tables):
    store(tables, RUN, 90.0, DEPLOYED + timedelta(hours=1))

    assert correct_stored_runs(*tables, ModelEnum.GFS, DEPLOYED, dry_run=False) == []
    assert directions(tables) == ([90.0], [90.0])


def test_a_dry_run_changes_nothing(tables):
    store(tables, RUN, 90.0, STORED)

    assert correct_stored_runs(*tables, ModelEnum.GFS, DEPLOYED, dry_run=True) == [RUN]
    assert directions(tables) == ([90.0], [90.0])


def test_an_older_run_does_not_undo_a_newer_one(tables):
    store(tables, RUN - timedelta(hours=6), 180.0, STORED)
    store(tables, RUN, 360.0, DEPLOYED + timedelta(hours=1))

    correct_stored_runs(*tables, ModelEnum.GFS, DEPLOYED, dry_run=False)

    assert directions(tables) == ([270.0, 360.0], [360.0])


def test_other_models_are_refused(tables):
    with pytest.raises(ValueError, match="never mirrored"):
        correct_stored_runs(*tables, ModelEnum.HRDPS, DEPLOYED, dry_run=False)


def test_a_time_in_the_future_is_refused(tables):
    later = datetime.now(UTC) + timedelta(hours=1)
    with pytest.raises(ValueError, match="future"):
        correct_stored_runs(*tables, ModelEnum.GFS, later, dry_run=False)
