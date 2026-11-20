"""The models whose grids are kept, and loading a run of one from the MSC datamart.

Each variable is kept as published, so that what is stored is exactly what was published.
"""

import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np

from wps_weather_data.grids.grib import GribScales, bc_crop, decode, grib_integers, read_field

DATAMART = "https://dd.weather.gc.ca/today"
SCALES = GribScales._fields


@dataclass(frozen=True)
class Variable:
    name: str
    units: str
    layer: str  # as in the datamart's file names
    # Accumulated since the run started: no field at hour 0, where it is zero.
    accumulated: bool = False


@dataclass(frozen=True)
class GridModel:
    name: str
    variables: tuple[Variable, ...]
    hours: tuple[int, ...]  # forecast hours kept
    # The UTC hour of the run kept in `history` each day: the model's last full-length run.
    history_run_hour: int
    folder: str  # on the datamart
    grid: str  # as in the datamart's file names

    def file_url(self, run_time: datetime, hour: int, variable: Variable) -> str:
        name = (
            f"{run_time:%Y%m%dT%H}Z_MSC_{self.name}_{variable.layer}_{self.grid}"
            f"_PT{hour:03d}H.grib2"
        )
        return f"{DATAMART}/{self.folder}/{run_time:%H}/{hour:03d}/{name}"


def _variables(temperature: str, humidity: str, speed: str, direction: str, precip: str):
    """The five fields the MSC jobs read, by layer name."""
    return (
        Variable("temperature", "K", temperature),
        Variable("relative_humidity", "%", humidity),
        Variable("wind_speed", "m/s", speed),
        Variable("wind_direction", "degrees", direction),
        Variable("precipitation", "mm since the run started", precip, accumulated=True),
    )


MODELS = {
    model.name: model
    for model in (
        GridModel(
            "HRDPS",
            _variables("TMP_AGL-2m", "RH_AGL-2m", "WIND_AGL-10m", "WDIR_AGL-10m", "APCP_Sfc"),
            hours=tuple(range(49)),
            history_run_hour=18,
            folder="model_hrdps/continental/2.5km",
            grid="RLatLon0.0225",
        ),
        GridModel(
            "RDPS",
            _variables(
                "AirTemp_AGL-2m",
                "RelativeHumidity_AGL-2m",
                "WindSpeed_AGL-10m",
                "WindDir_AGL-10m",
                "Precip-Accum_Sfc",
            ),
            hours=tuple(range(85)),
            history_run_hour=18,
            folder="model_rdps/10km",
            grid="RLatLon0.09",
        ),
    )
}


@dataclass
class RunGrid:
    """One model run over BC, as GRIB integers with each hour's scales."""

    model: GridModel
    run_time: datetime
    latitude: np.ndarray  # (y, x)
    longitude: np.ndarray
    integers: dict[str, np.ndarray]  # per variable, (hours, y, x) int32
    scales: dict[str, dict[str, np.ndarray]]  # per variable, {"reference": (hours,), ...}

    def values(self, name: str) -> np.ndarray:
        """A variable's decoded values, (hours, y, x)."""
        scales = (self.scales[name][s][:, np.newaxis, np.newaxis] for s in SCALES)
        return decode(self.integers[name], GribScales(*scales))


def download(url: str, path: Path, attempts: int = 3) -> Path:
    """Download `url` to `path` unless it is there. Retries a download that ends early; an HTTP
    error, such as 404 for a file not published yet, is raised at once."""
    partial = path.with_suffix(".part")
    for attempt in range(1, attempts + 1):
        if path.exists():
            break
        try:
            urllib.request.urlretrieve(url, partial)
            partial.rename(path)
        except urllib.error.HTTPError:
            raise
        except urllib.error.URLError:
            if attempt == attempts:
                raise
            time.sleep(attempt)
    return path


def load_run(model: GridModel, run_time: datetime, folder: Path) -> RunGrid:
    """Download a run into `folder` and read it, cropped to BC. Raises urllib.error.HTTPError
    (404) if any of its files is not published yet."""
    wanted = [
        (variable, hour)
        for variable in model.variables
        for hour in model.hours
        if not (variable.accumulated and hour == 0)
    ]

    def fetch(item: tuple[Variable, int]) -> Path:
        url = model.file_url(run_time, item[1], item[0])
        return download(url, folder / url.rsplit("/", 1)[1])

    with ThreadPoolExecutor(8) as pool:
        paths = list(pool.map(fetch, wanted))

    crop = bc_crop(paths[0])
    shape = (len(model.hours), crop.y.stop - crop.y.start, crop.x.stop - crop.x.start)
    # Hour 0 of an accumulated variable stays zero, which zero scales decode to.
    integers = {v.name: np.zeros(shape, np.int32) for v in model.variables}
    scales = {
        v.name: {s: np.zeros(len(model.hours), np.float64) for s in SCALES} for v in model.variables
    }
    for (variable, hour), path in zip(wanted, paths):
        values, field_scales = read_field(path)
        index = model.hours.index(hour)
        integers[variable.name][index] = grib_integers(values, field_scales)[crop.y, crop.x]
        for name, value in zip(SCALES, field_scales):
            scales[variable.name][name][index] = value
    return RunGrid(model, run_time, crop.latitude, crop.longitude, integers, scales)
