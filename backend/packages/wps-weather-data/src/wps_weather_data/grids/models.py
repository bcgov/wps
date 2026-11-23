"""The models whose grids are kept, and loading a run of one from where it is published.

Each variable is kept as published, so that what is stored is exactly what was published.
"""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np

from wps_weather_data.grids.grib import (
    Crop,
    GribScales,
    bc_crop,
    decode,
    grib_integers,
    read_field,
)
from wps_weather_data.grids.sources import EcmwfOpenData, MscDatamart, NoaaGfs, Source

SCALES = GribScales._fields


@dataclass(frozen=True)
class Variable:
    name: str
    units: str
    layer: str  # as the model's source names it
    # Accumulated since the run started: no field at hour 0, where it is zero.
    accumulated: bool = False


@dataclass(frozen=True)
class GridModel:
    name: str
    variables: tuple[Variable, ...]
    hours: tuple[int, ...]  # forecast hours kept
    # The UTC hour of the run kept in `history` each day: the model's last full-length run.
    history_run_hour: int
    source: Source
    run_hours: tuple[int, ...] = (0, 6, 12, 18)  # UTC hours the model runs at
    # The forecast hours of runs that do not have them all, by the UTC hour they run at.
    other_hours: dict[int, tuple[int, ...]] = field(default_factory=dict)

    def forecast_hours(self, run_time: datetime) -> tuple[int, ...]:
        """The forecast hours of a run."""
        return self.other_hours.get(run_time.hour, self.hours)


def _variables(temperature: str, humidity: str, speed: str, direction: str, precip: str):
    """The five fields the MSC jobs read, by layer name."""
    return (
        Variable("temperature", "K", temperature),
        Variable("relative_humidity", "%", humidity),
        Variable("wind_speed", "m/s", speed),
        Variable("wind_direction", "degrees", direction),
        Variable("precipitation", "mm since the run started", precip, accumulated=True),
    )


# The layer names GDPS and RDPS share.
_GDPS_RDPS_VARIABLES = _variables(
    "AirTemp_AGL-2m",
    "RelativeHumidity_AGL-2m",
    "WindSpeed_AGL-10m",
    "WindDir_AGL-10m",
    "Precip-Accum_Sfc",
)

MODELS = {
    model.name: model
    for model in (
        GridModel(
            "HRDPS",
            _variables("TMP_AGL-2m", "RH_AGL-2m", "WIND_AGL-10m", "WDIR_AGL-10m", "APCP_Sfc"),
            hours=tuple(range(49)),
            history_run_hour=18,
            source=MscDatamart("HRDPS", "model_hrdps/continental/2.5km", "RLatLon0.0225"),
        ),
        GridModel(
            "RDPS",
            _GDPS_RDPS_VARIABLES,
            hours=tuple(range(85)),
            history_run_hour=18,
            source=MscDatamart("RDPS", "model_rdps/10km", "RLatLon0.09"),
        ),
        GridModel(
            "GDPS",
            _GDPS_RDPS_VARIABLES,
            hours=tuple(range(0, 241, 3)),
            history_run_hour=12,
            source=MscDatamart("GDPS", "model_gdps/15km", "LatLon0.15"),
            run_hours=(0, 12),
        ),
        GridModel(
            "GFS",
            (
                Variable("temperature", "K", "TMP:2 m above ground:"),
                Variable("relative_humidity", "%", "RH:2 m above ground:"),
                Variable("wind_u", "m/s", "UGRD:10 m above ground:"),
                Variable("wind_v", "m/s", "VGRD:10 m above ground:"),
                # From the start (0-): most hours also have the last 3 or 6 hours' total.
                Variable(
                    "precipitation", "mm since the run started", "APCP:surface:0-", accumulated=True
                ),
            ),
            # GFS runs to 384 hours; ten days, as MoreCast uses.
            hours=tuple(range(0, 241, 3)),
            history_run_hour=18,
            source=NoaaGfs(),
        ),
        GridModel(
            "ECMWF",
            (
                Variable("temperature", "K", "2t"),
                Variable("dewpoint", "K", "2d"),
                Variable("wind_u", "m/s", "10u"),
                Variable("wind_v", "m/s", "10v"),
                # Unlike the others, it has a field for hour 0.
                Variable("precipitation", "m since the run started", "tp"),
            ),
            hours=tuple(range(0, 145, 3)) + tuple(range(150, 241, 6)),
            history_run_hour=12,
            source=EcmwfOpenData(),
            other_hours={hour: tuple(range(0, 145, 3)) for hour in (6, 18)},
        ),
    )
}


@dataclass
class VariableRun:
    """One variable of a run over BC, as GRIB integers with each hour's scales."""

    variable: Variable
    integers: np.ndarray  # (hours, y, x) int32
    scales: dict[str, np.ndarray]  # {"reference": (hours,), ...}

    def values(self) -> np.ndarray:
        """The decoded values, (hours, y, x)."""
        scales = (self.scales[s][:, np.newaxis, np.newaxis] for s in SCALES)
        return decode(self.integers, GribScales(*scales))


def run_published(model: GridModel, run_time: datetime) -> bool:
    """Whether all of a run is published. A run is published hour by hour, so it is complete once
    every variable's last hour is there."""
    last = model.forecast_hours(run_time)[-1]
    return all(model.source.exists(run_time, last, v.layer) for v in model.variables)


def _fetch(model: GridModel, run_time: datetime, hour: int, variable: Variable, folder: Path):
    path = folder / f"{variable.name}_{hour:03d}.grib2"
    model.source.fetch(run_time, hour, variable.layer, path)
    return path


def load_crop(model: GridModel, run_time: datetime, folder: Path) -> Crop:
    """The rows and columns of the model's grid covering BC, from one of the run's fields."""
    last = model.forecast_hours(run_time)[-1]
    path = _fetch(model, run_time, last, model.variables[0], folder)
    crop = bc_crop(path)
    path.unlink()
    return crop


def load_variable(
    model: GridModel, run_time: datetime, variable: Variable, crop: Crop, folder: Path
) -> VariableRun:
    """Download one variable of a run into `folder` and read it, cropped to BC. Each file is
    deleted once read, so a run's files never all take disk at once. Raises NotPublishedError if
    a field is not published."""
    run_hours = model.forecast_hours(run_time)
    # Hour 0 of an accumulated variable has no field and stays zero, which zero scales decode to.
    hours = [h for h in run_hours if not (variable.accumulated and h == 0)]
    with ThreadPoolExecutor(8) as pool:
        paths = list(pool.map(lambda h: _fetch(model, run_time, h, variable, folder), hours))
    shape = (len(run_hours), crop.y.stop - crop.y.start, crop.x.stop - crop.x.start)
    integers = np.zeros(shape, np.int32)
    scales = {s: np.zeros(len(run_hours), np.float64) for s in SCALES}
    for hour, path in zip(hours, paths):
        values, field_scales = read_field(path)
        path.unlink()
        index = run_hours.index(hour)
        # Cropped first: the check behind grib_integers copies the field a few times.
        integers[index] = grib_integers(values[crop.y, crop.x], field_scales)
        for name, value in zip(SCALES, field_scales):
            scales[name][index] = value
    return VariableRun(variable, integers, scales)
