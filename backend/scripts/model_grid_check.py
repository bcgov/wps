"""Check that the model grid stores are being kept: what each holds, and that it is right.

For each model's `recent` and `history` store, it prints the runs held and the latest run's
forecast at one location, and compares one forecast hour of every variable with the file on the
MSC datamart, which must match exactly. The datamart keeps about a day, so an older run cannot be
compared; it says so and does not count that as a failure.

It only reads. Exits 1 if a store is missing, is empty or does not match what was published.

It reads the backend's own S3 settings through wps_shared.config: OBJECT_STORE_SERVER,
OBJECT_STORE_USER_ID, OBJECT_STORE_SECRET and OBJECT_STORE_BUCKET. SUFFIX names the deployment to
check (`pr-123`, or `prod`) and is required, because with none set the stores would be
production's. From ./backend:

    SUFFIX=pr-123 uv run python scripts/model_grid_check.py

Design: docs/architecture/model-grid-storage-spike.md
"""

import sys
import tempfile
import urllib.error
from pathlib import Path

import numpy as np
from wps_shared import config
from wps_weather_data.grids.grib import read_field
from wps_weather_data.grids.models import MODELS, download, load_crop
from wps_weather_data.grids.store import GridStore

LATITUDE, LONGITUDE = 50.70, -120.44  # Kamloops
HOUR = 12
KELVIN = 273.15


def matches_datamart(store: GridStore, run_time) -> bool:
    """Whether every variable at `HOUR` of a run is what the datamart has. True if it no longer
    has the run."""
    model = store.model
    matches = True
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        try:
            crop = load_crop(model, run_time, folder)
            for variable in model.variables:
                path = folder / f"{variable.name}.grib2"
                download(model.file_url(run_time, HOUR, variable), path)
                values, _ = read_field(path)
                published = values[crop.y, crop.x].astype(np.float32)
                stored = store.read_map(run_time, HOUR, variable.name).astype(np.float32)
                same = np.array_equal(published, stored)
                matches = matches and same
                print(f"  {variable.name}, hour {HOUR}: {'matches' if same else 'DIFFERS'}")
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
            print("  not compared: the datamart no longer has this run")
    return matches


def check(store: GridStore) -> bool:
    name = f"{store.model.name} {store.store}"
    # Checked first, because reading a store that does not exist would create it.
    if not store.exists():
        print(f"{name}: does not exist")
        return False
    run_times = store.run_times()
    print(f"{name}: {len(run_times)} runs: {', '.join(f'{r:%m-%d %HZ}' for r in run_times)}")
    if not run_times:
        return False
    latest = run_times[-1]
    point = store.read_point(latest, *store.nearest_cell(LATITUDE, LONGITUDE))
    celsius = point["temperature"] - KELVIN
    print(
        f"  {latest:%m-%d %HZ} at {LATITUDE}, {LONGITUDE}: {celsius.size} hours, "
        f"{celsius.min():.1f} to {celsius.max():.1f} °C"
    )
    return matches_datamart(store, latest)


def main() -> int:
    if not config.get("SUFFIX"):
        print("Set SUFFIX to the deployment to check, such as pr-123, or prod.")
        return 1
    stores = [GridStore(model, name) for model in MODELS for name in ("recent", "history")]
    return 0 if all([check(store) for store in stores]) else 1


if __name__ == "__main__":
    sys.exit(main())
