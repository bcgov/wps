"""Add the columns WF1 and the data mart observe (`OBSERVED_COLUMNS`: the FWI System indices,
dewpoint, wind gust, grass curing, danger rating and observation validity) to `wf1`, `by_time` and
`by_station` tables that were created without them.

They are added in place, so every row already stored is kept, with nulls in them. Only a
deployment whose tables predate the columns needs it, and only once: a column a table has is
left alone, and a table that does not exist yet is skipped, because it is created with them.

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
from wps_weather_data.by_station import ByStationTable
from wps_weather_data.by_time import OBSERVED_COLUMNS, ByTimeTable
from wps_weather_data.wf1 import Wf1Table


def main() -> int:
    for table in (Wf1Table(), ByTimeTable(), ByStationTable()):
        if not table.exists():
            print(f"{table.table_uri} does not exist, skipped")
            continue
        delta_table = table.open()
        present = set(delta_table.schema().to_arrow().names)
        missing = [
            Field.from_arrow(pa.field(name, kind, nullable=True))
            for name, kind in OBSERVED_COLUMNS.items()
            if name not in present
        ]
        if missing:
            delta_table.alter.add_columns(missing)
        print(f"{table.table_uri}: added {len(missing)} columns")
    return 0


if __name__ == "__main__":
    sys.exit(main())
