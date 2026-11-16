"""Scheduled upkeep for the Delta Lake tables of station weather data.

Each table gets three chores: `optimize` merges the small files that appends and merges leave,
a checkpoint keeps the transaction log quick to open, and `vacuum` deletes files that no table
version within the retention window refers to.

Run with:  python -m wps_weather_data.maintenance

Design: docs/architecture/station-weather-storage.md
"""

import logging
import sys

from deltalake import DeltaTable
from wps_shared.wps_logging import configure_logging

from wps_weather_data.by_time import BY_TIME_KEY
from wps_weather_data.runs import RUNS_KEY
from wps_weather_data.store import resolve_table

logger = logging.getLogger(__name__)

TABLE_KEYS = (RUNS_KEY, BY_TIME_KEY)

# How far back a table can be read as it was. Files older than this that no current version
# refers to are deleted.
VACUUM_RETENTION_HOURS = 30 * 24


def maintain_table(
    table_uri: str,
    storage_options: dict[str, str] | None = None,
    *,
    retention_hours: int = VACUUM_RETENTION_HOURS,
    enforce_retention_duration: bool = True,
) -> dict:
    """Compact, checkpoint and vacuum one table. Returns what each step did."""
    table = DeltaTable(table_uri, storage_options=storage_options)
    compacted = table.optimize.compact()
    table.create_checkpoint()
    table.cleanup_metadata()
    deleted = table.vacuum(
        retention_hours=retention_hours,
        dry_run=False,
        enforce_retention_duration=enforce_retention_duration,
    )
    return {
        "files_added": compacted["numFilesAdded"],
        "files_removed": compacted["numFilesRemoved"],
        "files_deleted": len(deleted),
    }


def maintain_all() -> bool:
    """Maintain every table that exists. Returns False if any table failed."""
    succeeded = True
    for key in TABLE_KEYS:
        table_uri, storage_options = resolve_table(key, None, None)
        try:
            if not DeltaTable.is_deltatable(table_uri, storage_options=storage_options):
                logger.info("%s does not exist yet, skipping", key)
                continue
            result = maintain_table(table_uri, storage_options)
            logger.info("Maintained %s: %s", key, result)
        except Exception:
            # One table failing must not stop the others from being maintained.
            logger.exception("Failed to maintain %s", key)
            succeeded = False
    return succeeded


def main():
    configure_logging()
    sys.exit(0 if maintain_all() else 1)


if __name__ == "__main__":
    main()
