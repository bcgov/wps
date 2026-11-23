"""Keep a model's grids: write its new runs to `recent`, and the daily run to `history`.

Run hourly for each model, so a run is stored soon after the datamart has all of it:

    python -m wps_weather_data.grids.job --model HRDPS

Each time, it looks at the model's runs from the last day that `recent` (or, for the daily run,
`history`) does not have yet. A run the datamart has not finished publishing is skipped until
the next time. A run is downloaded and written a variable at a time, so only one variable's
files and values are held at once, and committed when all are written. Then it drops runs older than two days from `recent`; the nightly maintenance job
reclaims their space.

Design: docs/architecture/model-grid-storage-spike.md
"""

import argparse
import logging
import os
import sys
import tempfile
import urllib.error
from datetime import UTC, datetime, timedelta
from pathlib import Path

from wps_shared.chatops_notification import send_chatops_notification
from wps_shared.utils.time import get_utc_now
from wps_shared.wps_logging import configure_logging

from wps_weather_data.grids.models import (
    MODELS,
    GridModel,
    load_crop,
    load_variable,
    run_published,
)
from wps_weather_data.grids.store import GridStore, write_run

logger = logging.getLogger(__name__)

# How far back runs are looked for. The datamart keeps about a day.
LOOKBACK = timedelta(hours=24)
# How long `recent` keeps every run. Two days, so it never has a gap after midnight.
RECENT_WINDOW = timedelta(hours=48)


def run_times(model: GridModel, now: datetime) -> list[datetime]:
    """The model's runs that started within `LOOKBACK` of `now`, oldest first."""
    day = now.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    starts = [
        day + timedelta(days=offset, hours=hour) for offset in (-1, 0) for hour in model.run_hours
    ]
    return [start for start in starts if now - LOOKBACK <= start <= now]


def keep_grids(model: GridModel, recent: GridStore, history: GridStore, now: datetime) -> list:
    """Write the model's new runs and drop old ones from `recent`. Returns the runs written."""
    held = {recent: set(recent.run_times()), history: set(history.run_times())}
    written = []
    for run_time in run_times(model, now):
        stores = [recent, history] if run_time.hour == model.history_run_hour else [recent]
        targets = [store for store in stores if run_time not in held[store]]
        if not targets:
            continue
        if not run_published(model, run_time):
            logger.info("%s run %s is not all published yet", model.name, run_time)
            continue
        # One variable's files at a time, each deleted once read, in a folder of the run's own.
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            try:
                crop = load_crop(model, run_time, folder)
                variables = (
                    load_variable(model, run_time, variable, crop, folder)
                    for variable in model.variables
                )
                write_run(targets, run_time, crop, variables)
            except urllib.error.HTTPError as error:
                # A file gone missing part way: nothing was committed, so try again next time.
                if error.code != 404:
                    raise
                logger.info("%s run %s is missing %s", model.name, run_time, error.url)
                continue
        written.append(run_time)
    recent.delete_runs_before(now - RECENT_WINDOW)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--model", required=True, choices=sorted(MODELS))
    args = parser.parse_args()
    configure_logging()
    try:
        written = keep_grids(
            MODELS[args.model],
            GridStore(args.model, "recent"),
            GridStore(args.model, "history"),
            get_utc_now(),
        )
        logger.info("Stored %d %s runs: %s", len(written), args.model, written)
        return os.EX_OK
    except Exception as exception:
        logger.exception("Failed to keep %s grids", args.model)
        send_chatops_notification(f"Failed to keep {args.model} grids", exception)
        return os.EX_SOFTWARE


if __name__ == "__main__":
    sys.exit(main())
