from datetime import UTC, datetime, timedelta

import icechunk
import numpy as np
import pytest

from wps_weather_data.grids.grib import GribScales, decode, grib_integers
from wps_weather_data.grids.models import load_crop, load_variable
from wps_weather_data.grids.store import GridStore, write_run
from wps_weather_data.tests.grid_helpers import (
    HOURS,
    MODEL,
    RUN,
    fake_datamart,
    field,
    load_run,
    store,
    stored_bytes,
)


@pytest.fixture(autouse=True)
def datamart(monkeypatch, tmp_path):
    (tmp_path / "files").mkdir()
    return fake_datamart(monkeypatch)


@pytest.fixture
def run(tmp_path):
    return load_run(tmp_path / "files")


def test_grib_integers_decode_to_the_published_values():
    scales = GribScales(reference=2700.0, binary_scale=0, decimal_scale=1)
    values = np.array([270.0, 270.1, 285.5])

    integers = grib_integers(values, scales)

    assert integers.tolist() == [0, 1, 155]
    assert np.array_equal(decode(integers, scales), values)


def test_values_off_the_fields_steps_are_refused():
    scales = GribScales(reference=0.0, binary_scale=0, decimal_scale=1)
    with pytest.raises(ValueError, match="round-trip"):
        grib_integers(np.array([0.05]), scales)


def test_a_run_is_cropped_to_bc(run):
    crop, variables = run
    # BC is 48.2 to 60.1 N and 139.2 to 114 W: rows 60 to 49 N, columns 139 to 114 W.
    assert crop.latitude[:, 0].tolist() == list(range(60, 48, -1))
    assert crop.longitude[0].tolist() == list(range(-139, -113))
    assert variables["temperature"].integers.shape == (3, 12, 26)


def test_a_run_holds_exactly_what_was_published(run):
    # The crop starts at row 2 and column 3 of the full grid.
    published = field("T", 6)[2:14, 3:29].astype(np.float32)
    assert np.array_equal(run[1]["temperature"].values()[2].astype(np.float32), published)


def test_accumulated_precipitation_is_zero_at_hour_0(run):
    precipitation = run[1]["precipitation"].values()
    assert not precipitation[0].any()
    assert precipitation[1].any()


def test_each_file_is_deleted_once_read(tmp_path):
    folder = tmp_path / "files"
    crop = load_crop(MODEL, RUN, folder)
    load_variable(MODEL, RUN, MODEL.variables[0], crop, folder)

    assert not any(folder.iterdir())


def test_written_runs_read_back_exactly(tmp_path, run):
    crop, variables = run
    recent = store(tmp_path)

    assert recent.write_run(RUN, crop, variables.values())
    assert recent.run_times() == [RUN]

    y, x = recent.nearest_cell(50.1, -120.2)
    assert (float(crop.latitude[y, x]), float(crop.longitude[y, x])) == (50.0, -120.0)
    point = recent.read_point(RUN, y, x)
    assert point["forecast_hour"].tolist() == list(HOURS)
    assert np.array_equal(point["temperature"], variables["temperature"].values()[:, y, x])
    assert np.array_equal(
        recent.read_map(RUN, 3, "precipitation"), variables["precipitation"].values()[1]
    )


def test_a_run_goes_to_several_stores_in_one_pass(tmp_path, run):
    crop, variables = run
    recent, history = store(tmp_path, "recent"), store(tmp_path, "history")

    assert write_run([recent, history], RUN, crop, variables.values()) == [recent, history]
    assert recent.run_times() == history.run_times() == [RUN]


def test_a_run_already_stored_is_not_written_or_read_again(tmp_path, run):
    crop, variables = run
    recent = store(tmp_path)
    recent.write_run(RUN, crop, variables.values())

    def never():
        raise AssertionError("the run's variables were read again")
        yield

    assert not recent.write_run(RUN, crop, never())
    assert recent.run_times() == [RUN]


def test_a_run_missing_a_variable_is_not_committed(tmp_path, run):
    crop, variables = run
    recent = store(tmp_path)

    with pytest.raises(ValueError, match="the run has"):
        recent.write_run(RUN, crop, [variables["temperature"]])
    assert recent.run_times() == []


def test_a_location_outside_bc_is_refused(tmp_path, run):
    recent = store(tmp_path)
    recent.write_run(RUN, run[0], run[1].values())
    with pytest.raises(ValueError, match="outside BC"):
        recent.nearest_cell(45.0, -120.0)


def test_old_runs_are_deleted_and_their_space_collected(tmp_path):
    recent = store(tmp_path)
    for hours_ago in (18, 12, 6, 0):
        run_time = RUN - timedelta(hours=hours_ago)
        crop, variables = load_run(tmp_path / "files", run_time)
        recent.write_run(run_time, crop, variables.values())
    size = stored_bytes(tmp_path)

    deleted = recent.delete_runs_before(RUN - timedelta(hours=6))
    result = recent.maintain(
        datetime.now(UTC), snapshot_retention=timedelta(0), object_grace=timedelta(0)
    )

    assert deleted == [RUN - timedelta(hours=18), RUN - timedelta(hours=12)]
    assert recent.run_times() == [RUN - timedelta(hours=6), RUN]
    assert result["chunks_deleted"] > 0
    assert result["objects_failed_to_delete"] == 0
    assert stored_bytes(tmp_path) < size
    assert recent.read_point(RUN, 0, 0)["temperature"].size == len(HOURS)


def test_stores_of_different_models_are_refused_together(tmp_path, run):
    other = GridStore("HRDPS", "recent", icechunk.local_filesystem_storage(str(tmp_path / "x")))
    with pytest.raises(ValueError, match="one model"):
        write_run([store(tmp_path), other], RUN, run[0], run[1].values())


def test_an_empty_store_has_no_runs(tmp_path):
    assert store(tmp_path).run_times() == []
