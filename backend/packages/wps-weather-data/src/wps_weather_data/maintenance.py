"""Scheduled upkeep for the Delta Lake tables of station weather data.

Run with:  python -m wps_weather_data.maintenance

Design: docs/architecture/station-weather-storage.md
"""

import logging
import sys
from collections.abc import Iterable

from wps_shared.wps_logging import configure_logging

from wps_weather_data.by_time import ByTimeTable
from wps_weather_data.runs import RunsTable
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


def main():
    configure_logging()
    sys.exit(0 if maintain_all([RunsTable(), ByTimeTable()]) else 1)


if __name__ == "__main__":
    main()
