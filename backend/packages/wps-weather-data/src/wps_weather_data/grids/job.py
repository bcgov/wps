"""Keep a model's grids: write its new runs to `recent`, and the daily run to `history`.

Run hourly for each model, so a run is stored soon after all of it is published:

    python -m wps_weather_data.grids.job --model HRDPS

Each time, it looks at the model's runs from the last day that `recent` (or, for the daily run,
`history`) does not have yet. A run not all published yet is skipped until
the next time. A run is downloaded and written a variable at a time, so only one variable's
files and values are held at once, and committed when all are written. Then it drops runs older
than two days from `recent`; the nightly maintenance job reclaims their space.

A store that cannot be written to does not hold up the other, and the job fails at the end.

Design: docs/architecture/model-grid-storage-spike.md
"""

import argparse
import logging
import os
import sys
import tempfile
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
from wps_weather_data.grids.sources import NotPublishedError
from wps_weather_data.grids.store import GridStore, write_run

logger = logging.getLogger(__name__)

# How far back runs are looked for. The MSC datamart keeps about a day.
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
    """Write the model's new runs and drop old ones from `recent`. Returns the runs written.

    The stores are independent: one that fails is left alone for the rest of this time, the other
    is still kept, and the errors are raised together at the end."""
    failures: dict[GridStore, Exception] = {}
    held: dict[GridStore, set[datetime]] = {}
    # `history` first: it is the one that is kept, and runs are committed in this order.
    for store in (history, recent):
        try:
            held[store] = set(store.run_times())
        except Exception as error:
            logger.exception("Failed to read the %s %s store", model.name, store.store)
            failures[store] = error
    written = []
    for run_time in run_times(model, now):
        stores = [history, recent] if run_time.hour == model.history_run_hour else [recent]
        targets = [s for s in stores if s not in failures and run_time not in held[s]]
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
                stored, failed = write_run(targets, run_time, crop, variables)
            except NotPublishedError as error:
                # A field gone missing part way: nothing was committed, so try again next time.
                logger.info("%s run %s is missing %s", model.name, run_time, error)
                continue
        failures.update(failed)
        if stored:
            written.append(run_time)
    if recent not in failures:
        try:
            recent.delete_runs_before(now - RECENT_WINDOW)
        except Exception as error:
            logger.exception("Failed to delete old runs from the %s recent store", model.name)
            failures[recent] = error
    if failures:
        names = " and ".join(store.store for store in failures)
        raise ExceptionGroup(
            f"Failed to keep {model.name} {names}; stored {len(written)} runs",
            list(failures.values()),
        )
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
