"""Bring station weather tables created by earlier code up to date.

- Add the columns WF1 and the data mart observe (`OBSERVED_COLUMNS`: the FWI System indices,
  dewpoint, wind gust, grass curing, danger rating and observation validity) to `wf1`,
  `by_time` and `by_station`. They are added in place, so every row already stored is kept,
  with nulls in them.
- Set `TABLE_CONFIGURATION` on every table, so it checkpoints itself as it is written, and
  write a checkpoint now.

Only a deployment whose tables predate these needs it, and running it again changes nothing: a
column or property a table has is left alone, and a table that does not exist yet is skipped,
because it is created with them.

Run it right after deploying the code that writes the columns. Code from before them cannot
write to a table that has them, and the new code cannot write to a table that lacks them.

Run from ./backend against the deployment's bucket:

    uv run python scripts/station_weather_add_columns.py

Then backfill the values from the data mart and rebuild `by_station`, as
docs/DATA_REPROCESSING.md describes.

Design: docs/architecture/station-weather-storage.md
"""

import sys

import pyarrow as pa
from deltalake.schema import Field
from wps_shared.weather_models import ModelEnum
from wps_weather_data.by_station import ByStationTable
from wps_weather_data.by_time import OBSERVED_COLUMNS, ByTimeTable
from wps_weather_data.runs import RunsTable
from wps_weather_data.staging import StagingTable
from wps_weather_data.stations import StationsTable
from wps_weather_data.table import TABLE_CONFIGURATION, DeltaWeatherTable
from wps_weather_data.wf1 import Wf1Table


def add_columns(table: DeltaWeatherTable) -> int:
    """Add the observed columns the table lacks. Returns how many it added."""
    delta_table = table.open()
    present = set(delta_table.schema().to_arrow().names)
    missing = [
        Field.from_arrow(pa.field(name, kind, nullable=True))
        for name, kind in OBSERVED_COLUMNS.items()
        if name not in present
    ]
    if missing:
        delta_table.alter.add_columns(missing)
    return len(missing)


def configure(table: DeltaWeatherTable) -> bool:
    """Set the table properties it lacks and checkpoint it. Returns whether any were set."""
    delta_table = table.open()
    configuration = delta_table.metadata().configuration
    changed = {
        key: value for key, value in TABLE_CONFIGURATION.items() if configuration.get(key) != value
    }
    if changed:
        delta_table.alter.set_table_properties(changed)
    delta_table.create_checkpoint()
    return bool(changed)


def main() -> int:
    with_columns = (Wf1Table, ByTimeTable, ByStationTable)
    tables = [
        Wf1Table,
        ByTimeTable,
        ByStationTable,
        RunsTable,
        StationsTable,
        *(lambda model=model: StagingTable(model) for model in ModelEnum),
    ]
    for make_table in tables:
        # One table at a time, so only one is held open.
        table = make_table()
        if not table.exists():
            print(f"{table.table_uri} does not exist, skipped")
            continue
        added = add_columns(table) if make_table in with_columns else 0
        configured = configure(table)
        print(
            f"{table.table_uri}: added {added} columns, "
            f"{'set' if configured else 'already had'} its properties, checkpointed"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
