"""Report the size of the `wf1` Delta table in object storage.

Prints the size, file count and row count of the table's current version, in total and for each
source and resolution. Files that a later commit replaced are not counted: they stay in the
bucket until the maintenance job vacuums them, as does the transaction log.

Run from ./backend against the deployment's bucket:

    uv run python scripts/station_wf1_table_size.py

Design: docs/architecture/station-weather-storage.md
"""

import sys
from collections import defaultdict

import pyarrow as pa
from wps_weather_data.wf1 import Wf1Table


def main() -> int:
    table = Wf1Table()
    if not table.exists():
        print(f"{table.table_uri} does not exist")
        return 1

    files = pa.table(table.open().get_add_actions(flatten=True)).to_pylist()
    # (source, resolution) -> [bytes, files, rows]
    groups: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0, 0])
    for file in files:
        group = groups[(file["partition.source"], file["partition.resolution"])]
        group[0] += file["size_bytes"]
        group[1] += 1
        group[2] += file["num_records"]

    print(table.table_uri)
    for (source, resolution), (size, count, rows) in sorted(groups.items()):
        print(
            f"  {source:<9} {resolution:<7} {size / 1e6:>9.1f} MB {count:>7} files {rows:>11} rows"
        )
    size, count, rows = (sum(group[index] for group in groups.values()) for index in range(3))
    print(f"  {'total':<17} {size / 1e6:>9.1f} MB {count:>7} files {rows:>11} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
