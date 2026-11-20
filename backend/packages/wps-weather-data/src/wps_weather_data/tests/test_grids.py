from datetime import UTC, datetime, timedelta
from pathlib import Path

import eccodes
import icechunk
import numpy as np
import pytest

from wps_weather_data.grids import models
from wps_weather_data.grids.grib import GribScales, decode, grib_integers
from wps_weather_data.grids.models import GridModel, Variable, load_run
from wps_weather_data.grids.store import GridStore

RUN = datetime(2026, 11, 19, 18, tzinfo=UTC)
# A 1 degree grid around BC, north to south: 18 rows from 62 N, 33 columns from 142 W.
LATITUDES = np.arange(62.0, 44.0, -1.0)
LONGITUDES = np.arange(-142.0, -109.0, 1.0)
HOURS = (0, 3, 6)
OFFSETS = {"T": 270.0, "P": 0.0}

MODEL = GridModel(
    "TEST",
    (
        Variable("temperature", "K", "T"),
        Variable("precipitation", "mm", "P", accumulated=True),
    ),
    hours=HOURS,
    history_run_hour=18,
    folder="test",
    grid="LatLon1",
)


def field(layer: str, hour: int) -> np.ndarray:
    """Values that differ by cell and hour, on the field's 0.1 steps."""
    rows, columns = np.meshgrid(range(len(LATITUDES)), range(len(LONGITUDES)), indexing="ij")
    return np.round(OFFSETS[layer] + rows + columns / 10 + hour, 1)


def write_grib(path: Path, values: np.ndarray) -> Path:
    """A GRIB2 file of one field on the test grid, simply packed to 0.1."""
    handle = eccodes.codes_grib_new_from_samples("regular_ll_sfc_grib2")
    for key, value in {
        "Ni": len(LONGITUDES),
        "Nj": len(LATITUDES),
        "latitudeOfFirstGridPointInDegrees": LATITUDES[0],
        "latitudeOfLastGridPointInDegrees": LATITUDES[-1],
        "longitudeOfFirstGridPointInDegrees": LONGITUDES[0] + 360,
        "longitudeOfLastGridPointInDegrees": LONGITUDES[-1] + 360,
        "iDirectionIncrementInDegrees": 1.0,
        "jDirectionIncrementInDegrees": 1.0,
        "jScansPositively": 0,
        "packingType": "grid_simple",
        "bitsPerValue": 16,
        "decimalScaleFactor": 1,
    }.items():
        eccodes.codes_set(handle, key, value)
    eccodes.codes_set_values(handle, values.ravel())
    with open(path, "wb") as out:
        eccodes.codes_write(handle, out)
    eccodes.codes_release(handle)
    return path


@pytest.fixture(autouse=True)
def test_model(monkeypatch):
    monkeypatch.setitem(models.MODELS, "TEST", MODEL)

    def download(url: str, path: Path) -> Path:
        # ..._MSC_TEST_{layer}_LatLon1_PT{hour}H.grib2
        layer, hour = url.split("_MSC_TEST_")[1].split("_")[0], int(url[-10:-7])
        if layer == "P" and hour == 0:
            raise AssertionError("there is no precipitation file for hour 0")
        return write_grib(path, field(layer, hour))

    monkeypatch.setattr(models, "download", download)


@pytest.fixture
def run(tmp_path):
    return load_run(MODEL, RUN, tmp_path)


def store(tmp_path, name="recent") -> GridStore:
    storage = icechunk.local_filesystem_storage(str(tmp_path / "stores" / name))
    return GridStore("TEST", name, storage)


def stored_bytes(tmp_path) -> int:
    return sum(p.stat().st_size for p in (tmp_path / "stores").rglob("*") if p.is_file())


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
    # BC is 48.2 to 60.1 N and 139.2 to 114 W: rows 60 to 49 N, columns 139 to 114 W.
    assert run.latitude[:, 0].tolist() == list(range(60, 48, -1))
    assert run.longitude[0].tolist() == list(range(-139, -113))
    assert run.integers["temperature"].shape == (3, 12, 26)


def test_a_run_holds_exactly_what_was_published(run):
    # The crop starts at row 2 and column 3 of the full grid.
    published = field("T", 6)[2:14, 3:29].astype(np.float32)
    assert np.array_equal(run.values("temperature")[2].astype(np.float32), published)


def test_accumulated_precipitation_is_zero_at_hour_0(run):
    assert not run.values("precipitation")[0].any()
    assert run.values("precipitation")[1].any()


def test_written_runs_read_back_exactly(tmp_path, run):
    recent = store(tmp_path)

    assert recent.write_run(run)
    assert recent.run_times() == [RUN]

    y, x = recent.nearest_cell(50.1, -120.2)
    assert (float(run.latitude[y, x]), float(run.longitude[y, x])) == (50.0, -120.0)
    point = recent.read_point(RUN, y, x)
    assert point["forecast_hour"].tolist() == list(HOURS)
    assert np.array_equal(point["temperature"], run.values("temperature")[:, y, x])
    assert np.array_equal(recent.read_map(RUN, 3, "precipitation"), run.values("precipitation")[1])


def test_a_run_already_stored_is_not_written_again(tmp_path, run):
    recent = store(tmp_path)
    recent.write_run(run)

    assert not recent.write_run(run)
    assert recent.run_times() == [RUN]


def test_a_location_outside_bc_is_refused(tmp_path, run):
    recent = store(tmp_path)
    recent.write_run(run)
    with pytest.raises(ValueError, match="outside BC"):
        recent.nearest_cell(45.0, -120.0)


def test_old_runs_are_deleted_and_their_space_collected(tmp_path):
    recent = store(tmp_path)
    for hours_ago in (18, 12, 6, 0):
        recent.write_run(load_run(MODEL, RUN - timedelta(hours=hours_ago), tmp_path))
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


def test_a_run_of_another_model_is_refused(tmp_path, run):
    other = GridStore("HRDPS", "recent", icechunk.local_filesystem_storage(str(tmp_path / "x")))
    with pytest.raises(ValueError, match="cannot go in"):
        other.write_run(run)


def test_an_empty_store_has_no_runs(tmp_path):
    assert store(tmp_path).run_times() == []
