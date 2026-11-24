"""Correcting the GFS and NAM wind directions stored before the station job computed them right.

The job took u for v when it made a direction from the GRIB's wind components, so every direction
was mirrored: 90 - the right one. The bias adjusted directions were not affected, because the
regression behind them has both components as inputs and learned them the wrong way round.

That is also why the stored history has to be corrected, and not only what is stored from now on.
Bias adjustment trains on the last 19 days of `runs`, and would be wrong until those had passed.
"""

import logging
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime

import pyarrow.compute as pc
from wps_shared.weather_models import ModelEnum

from wps_weather_data.by_time import ByTimeTable
from wps_weather_data.runs import RunsTable

logger = logging.getLogger(__name__)

# The models whose wind is published as components and read by that code.
MIRRORED_MODELS = (ModelEnum.GFS, ModelEnum.NAM)


def corrected_direction(stored: float | None) -> float | None:
    """The right wind direction for one that was stored mirrored. North is 360, as the job has it."""
    if stored is None:
        return None
    return (90.0 - stored) % 360 or 360.0


def corrected_rows(model: ModelEnum, rows: Iterable[Mapping]) -> list[dict]:
    """A run's rows, stored by the old code, with their wind directions corrected."""
    if model not in MIRRORED_MODELS:
        return [dict(row) for row in rows]
    return [{**row, "wdir_tgl_10": corrected_direction(row["wdir_tgl_10"])} for row in rows]


def correct_stored_runs(
    runs: RunsTable, by_time: ByTimeTable, model: ModelEnum, before: datetime, dry_run: bool
) -> list[datetime]:
    """Correct every run of a model whose newest version was stored before `before`, when the
    fixed job was deployed. A corrected run is appended to `runs` as a new version and merged into
    `by_time`. It is then newer than `before`, so doing this again leaves it alone. Returns the
    runs corrected."""
    if model not in MIRRORED_MODELS:
        raise ValueError(f"{model.value} wind directions were never mirrored")
    if before > datetime.now(UTC):
        # A corrected run would still be older than it, and be mirrored again next time.
        raise ValueError(f"{before} is in the future")
    if not runs.exists():
        return []
    run_timestamps = pc.unique(
        runs.dataset().to_table(columns=["run_ts"], filter=pc.field("model") == model.value)[
            "run_ts"
        ]
    ).to_pylist()
    corrected = []
    for run_ts in sorted(run_timestamps):
        if runs.newest_version(model, run_ts) >= before:
            continue
        if not dry_run:
            rows = corrected_rows(model, runs.read(model, run_ts, run_ts).to_pylist())
            # by_time first: if it fails, the run is still old here and is done again.
            by_time.merge_run(model, run_ts, rows)
            runs.append_run(model, run_ts, rows)
        corrected.append(run_ts)
    return corrected
