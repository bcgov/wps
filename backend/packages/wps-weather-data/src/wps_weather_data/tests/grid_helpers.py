"""A test model and a fake MSC datamart for the grids tests."""

import urllib.error
from datetime import UTC, datetime
from pathlib import Path

import eccodes
import icechunk
import numpy as np

from wps_weather_data.grids import models
from wps_weather_data.grids import store as store_module
from wps_weather_data.grids.grib import Crop
from wps_weather_data.grids.models import (
    GridModel,
    Variable,
    VariableRun,
    load_crop,
    load_variable,
)
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


def fake_datamart(
    monkeypatch, unpublished: set[str] = frozenset(), vanished: set[str] = frozenset()
) -> list[str]:
    """Register the test model and serve its files from a fake datamart. Runs (as YYYYMMDDTHH)
    in `unpublished` are not there at all; runs in `vanished` look published but their
    downloads answer 404. Returns the URLs downloaded."""
    monkeypatch.setitem(models.MODELS, "TEST", MODEL)
    downloaded = []

    def parse(url: str) -> tuple[str, str, int]:
        # .../{YYYYMMDD}T{HH}Z_MSC_TEST_{layer}_LatLon1_PT{hour}H.grib2
        name = url.rsplit("/", 1)[1]
        run, rest = name.split("Z_MSC_TEST_")
        return run, rest.split("_")[0], int(name[-10:-7])

    def url_exists(url: str) -> bool:
        return parse(url)[0] not in unpublished

    def download(url: str, path: Path) -> Path:
        run, layer, hour = parse(url)
        if layer == "P" and hour == 0:
            raise AssertionError("there is no precipitation file for hour 0")
        if run in unpublished | vanished:
            raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
        downloaded.append(url)
        return write_grib(path, field(layer, hour))

    monkeypatch.setattr(models, "url_exists", url_exists)
    monkeypatch.setattr(models, "download", download)
    return downloaded


def load_run(folder: Path, run_time: datetime = RUN) -> tuple[Crop, dict[str, VariableRun]]:
    """A whole run of the test model: its crop, and each variable."""
    crop = load_crop(MODEL, run_time, folder)
    variables = {v.name: load_variable(MODEL, run_time, v, crop, folder) for v in MODEL.variables}
    return crop, variables


def store(tmp_path, name="recent") -> GridStore:
    storage = icechunk.local_filesystem_storage(str(tmp_path / "stores" / name))
    return GridStore("TEST", name, storage)


def refuse_writes(monkeypatch, refused: GridStore, step: str):
    """Make a store fail when a run is written to it, at `step`: "add" or "commit"."""
    original = getattr(store_module._RunWriter, step)

    def write(writer, *args):
        if writer.store is refused:
            raise OSError("refused")
        return original(writer, *args)

    monkeypatch.setattr(store_module._RunWriter, step, write)


def stored_bytes(tmp_path) -> int:
    return sum(p.stat().st_size for p in (tmp_path / "stores").rglob("*") if p.is_file())
