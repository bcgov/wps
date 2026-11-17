"""Historical station observations from the BCWS data mart, as `ACTUALS` rows.

The data mart publishes every station's hourly observations as CSV files, back to 1987:
https://www.for.gov.bc.ca/ftp/HPR/external/!publish/BCWS_DATA_MART/. A year's folder holds one
file for the whole year (`1987_BCWS_WX_OBS.csv`), and from 2022 a file per day as well
(`2026-11-16.csv`). The current year has only the daily files.

This reads those files into rows with the `by_time` columns and writes them the way the hourly
actuals job writes what it fetches from WF1: appended to `wf1` and merged into `by_time`. Each
station's noon row also carries WF1's daily values, and becomes a daily row as well.
`data_mart_backfill` downloads the files and runs it.

Design: docs/architecture/station-weather-storage.md
"""

import csv
import logging
from collections.abc import Iterable, Iterator
from datetime import timedelta

import pyarrow as pa
import pyarrow.compute as pc

from wps_weather_data.by_time import ACTUALS, BY_TIME_SCHEMA, DAILY, HOURLY, ByTimeTable
from wps_weather_data.wf1 import VALID_RANGES, Wf1Table

logger = logging.getLogger(__name__)

# The files give the time as YYYYMMDDHH in Pacific Standard Time all year.
_PST_TO_UTC = timedelta(hours=8)
# The hour 12 row, 20:00 UTC, also carries WF1's daily values. This is its precip total for the
# 24 hours before.
_DAILY_HOUR = "12"
_DAILY_PRECIPITATION = "PRECIPITATION"

# by_time column -> data mart column.
_COLUMNS = {
    "temperature": "HOURLY_TEMPERATURE",
    "relative_humidity": "HOURLY_RELATIVE_HUMIDITY",
    "wind_speed": "HOURLY_WIND_SPEED",
    "wind_direction": "HOURLY_WIND_DIRECTION",
    "precipitation": "HOURLY_PRECIPITATION",
}

_BATCH_ROWS = 200_000


def _number(text: str, column: str) -> float | None:
    """The value if it is a number in the column's valid range, else None."""
    try:
        value = float(text)
    except ValueError:
        return None
    low, high = VALID_RANGES[column]
    # A NaN fails the comparison.
    return value if low <= value <= high else None


class _Rows:
    """Rows of one resolution being collected from a file."""

    def __init__(self, resolution: str):
        self.resolution = resolution
        self.station_codes: list[int] = []
        self.times: list[str] = []
        self.values: dict[str, list] = {column: [] for column in _COLUMNS}

    def __len__(self) -> int:
        return len(self.station_codes)

    def add(self, station_code: int, time: str, values: dict[str, float | None]):
        self.station_codes.append(station_code)
        self.times.append(time)
        for column, value in values.items():
            self.values[column].append(value)

    def to_table(self) -> pa.Table:
        local = pc.strptime(pa.array(self.times, pa.string()), format="%Y%m%d%H", unit="us")
        timestamp = pc.add(local, pa.scalar(_PST_TO_UTC, pa.duration("us"))).cast(
            BY_TIME_SCHEMA.field("timestamp").type
        )
        count = len(self)
        columns = {
            "resolution": pa.array([self.resolution] * count, pa.string()),
            "source": pa.array([ACTUALS] * count, pa.string()),
            "month": pc.strftime(timestamp, format="%Y-%m"),
            "station_code": pa.array(self.station_codes, pa.int32()),
            "timestamp": timestamp,
            "run_ts": pa.nulls(count, BY_TIME_SCHEMA.field("run_ts").type),
            # When each observation was first fetched is not known. Using its own time means a
            # value the hourly job fetched from WF1 is never replaced by one from here.
            "ingested_at": timestamp,
        }
        for field in BY_TIME_SCHEMA:
            if field.name not in columns:
                columns[field.name] = (
                    pa.array(self.values[field.name], field.type)
                    if field.name in self.values
                    else pa.nulls(count, field.type)
                )
        return pa.table(
            {name: columns[name] for name in BY_TIME_SCHEMA.names}, schema=BY_TIME_SCHEMA
        )


def read_observations(lines: Iterable[str]) -> Iterator[pa.Table]:
    """Read a data mart observations file as `ACTUALS` rows, a batch at a time.

    Every row with a value becomes an hourly row. A noon row with a daily precip total also
    becomes a daily row: the noon observation with that total, which is what WF1's daily
    actual holds. A value that is missing or outside its valid range is null, as for WF1.
    """
    hourly = _Rows(HOURLY)
    daily = _Rows(DAILY)
    for record in csv.DictReader(lines):
        values = {column: _number(record[name] or "", column) for column, name in _COLUMNS.items()}
        station_code = int(record["STATION_CODE"])
        time = record["DATE_TIME"]
        if any(value is not None for value in values.values()):
            hourly.add(station_code, time, values)
        if time.endswith(_DAILY_HOUR):
            total = _number(record.get(_DAILY_PRECIPITATION) or "", "precipitation")
            if total is not None:
                daily.add(station_code, time, {**values, "precipitation": total})
        if len(hourly) >= _BATCH_ROWS:
            yield hourly.to_table()
            hourly = _Rows(HOURLY)
    for rows in (hourly, daily):
        if len(rows):
            yield rows.to_table()


def read_observations_file(path: str) -> Iterator[pa.Table]:
    """Read a downloaded data mart observations file. Some files start with a byte order mark."""
    with open(path, encoding="utf-8-sig", newline="") as lines:
        yield from read_observations(lines)


def one_per_station_and_time(rows: pa.Table) -> pa.Table:
    """Keep the last row of each station, time and resolution. Some files repeat rows."""
    position = pa.array(range(rows.num_rows), pa.int64())
    last = (
        rows.append_column("position", position)
        .group_by(["resolution", "station_code", "timestamp"])
        .aggregate([("position", "max")])
    )
    kept = last["position_max"].combine_chunks()
    return rows.take(kept.take(pc.sort_indices(kept)))


def write_observations(wf1: Wf1Table, by_time: ByTimeTable, rows: pa.Table) -> dict[str, int]:
    """Write `ACTUALS` rows to `wf1` and `by_time`, a month at a time. Returns how many rows
    were read, how many of those are daily, and how many went to each table.

    Writing the same rows again changes nothing: `wf1` only takes a row that differs from the
    version before it, and `by_time` keeps a row that was fetched from WF1.
    """
    rows = one_per_station_and_time(rows)
    written = {
        "read": rows.num_rows,
        "daily": rows.filter(pc.equal(rows["resolution"], DAILY)).num_rows,
        "wf1": 0,
        "by_time": 0,
    }
    for month in sorted(pc.unique(rows["month"]).to_pylist()):
        chunk = rows.filter(pc.equal(rows["month"], month))
        written["wf1"] += wf1.append_changed(chunk).num_rows
        written["by_time"] += by_time.merge_wf1_rows(chunk)
        logger.info("Wrote %d observations for %s", chunk.num_rows, month)
    return written
