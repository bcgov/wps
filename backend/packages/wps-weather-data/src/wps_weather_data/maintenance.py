"""Scheduled upkeep for the Delta Lake tables of station weather data, and the model grid stores.

Run with:  python -m wps_weather_data.maintenance

Design: docs/architecture/station-weather-storage.md and model-grid-storage-spike.md
"""

import logging
import sys
from collections.abc import Iterable, Iterator
from datetime import datetime

from wps_shared.weather_models import ModelEnum
from wps_shared.utils.time import get_utc_now
from wps_shared.wps_logging import configure_logging

from wps_weather_data.by_station import ByStationTable
from wps_weather_data.by_time import ByTimeTable
from wps_weather_data.grids.models import MODELS
from wps_weather_data.grids.store import GridStore
from wps_weather_data.runs import RunsTable
from wps_weather_data.staging import StagingTable
from wps_weather_data.stations import StationsTable
from wps_weather_data.wf1 import Wf1Table
from wps_weather_data.table import DeltaWeatherTable

logger = logging.getLogger(__name__)


def maintain_all(tables: Iterable[DeltaWeatherTable]) -> bool:
    """Maintain every table that exists. Returns False if any table failed."""
    succeeded = True
    for table in tables:
        try:
            if not table.exists():
                logger.info("%s does not exist yet, skipping", table.table_uri)
                continue
            result = table.maintain()
            logger.info("Maintained %s: %s", table.table_uri, result)
        except Exception:
            # One table failing must not stop the others from being maintained.
            logger.exception("Failed to maintain %s", table.table_uri)
            succeeded = False
    return succeeded


def all_tables() -> Iterator[DeltaWeatherTable]:
    """Every table, created as it is reached. An open table holds its log state in memory, so
    creating them one at a time keeps only one open."""
    yield RunsTable()
    yield ByTimeTable()
    yield Wf1Table()
    yield ByStationTable()
    yield StationsTable()
    for model in ModelEnum:
        yield StagingTable(model)


def all_grid_stores() -> Iterator[GridStore]:
    """Each model's `recent` and `history` grid stores, created as they are reached."""
    for model in MODELS:
        for store in ("recent", "history"):
            yield GridStore(model, store)


def maintain_grids(stores: Iterable[GridStore], now: datetime) -> bool:
    """Expire snapshots and garbage collect every grid store that exists, reclaiming the space of
    the runs deleted from it. Returns False if any store failed."""
    succeeded = True
    for store in stores:
        name = f"{store.model.name} {store.store}"
        try:
            if not store.exists():
                logger.info("The %s grid store does not exist yet, skipping", name)
                continue
            result = store.maintain(now)
            logger.info("Maintained the %s grid store: %s", name, result)
            succeeded = succeeded and not result["objects_failed_to_delete"]
        except Exception:
            # One store failing must not stop the others from being maintained.
            logger.exception("Failed to maintain the %s grid store", name)
            succeeded = False
    return succeeded


def main():
    configure_logging()
    tables = maintain_all(all_tables())
    grids = maintain_grids(all_grid_stores(), get_utc_now())
    sys.exit(0 if tables and grids else 1)


if __name__ == "__main__":
    main()
