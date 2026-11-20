"""The `by_station` dataset: the `by_time` rows laid out by station, as a Delta Lake table in
object storage.

`by_time` is laid out by month, which suits a read of every station for a few days. Climatology
reads the other way, one station across every year, and in `by_time` that touches a file per
month holding every station. Here the same rows are partitioned by resolution, station and year,
so a station's record is its own files and nothing else is read.

One job is the only writer. Each night it replaces the current year's rows from `by_time`, in
one commit per resolution, so a reader sees a year either as it was or as it now is. The table
is derived, lags `by_time` by up to a day, and can be rebuilt at any time:

    python -m wps_weather_data.by_station                    the nightly run
    python -m wps_weather_data.by_station --from-year 1987   rebuild from a year onwards

A year that has ended is only rebuilt when asked for, which is how a backfill of earlier years,
or a correction to one, reaches this table.

Design: docs/architecture/station-weather-storage.md
"""

import argparse
import logging
import sys
from collections.abc import Iterable, Sequence

import pyarrow as pa
import pyarrow.compute as pc
from deltalake import WriterProperties, write_deltalake
from wps_shared.sfms.raster_addresser import S3Key
from wps_shared.utils.time import get_utc_now
from wps_shared.wps_logging import configure_logging

from wps_weather_data.addresser import StationWeatherAddresser
from wps_weather_data.by_time import BY_TIME_SCHEMA, DAILY, HOURLY, ByTimeTable
from wps_weather_data.table import TABLE_CONFIGURATION, DeltaWeatherTable

logger = logging.getLogger(__name__)

PARTITION_COLUMNS = ["resolution", "station_code", "year"]

# The by_time columns, with the UTC year in place of the month.
BY_STATION_SCHEMA = pa.schema(
    [
        *(field for field in BY_TIME_SCHEMA if field.name != "month"),
        ("year", pa.int32()),
    ]
)

# What a read of several stations returns: the resolution was asked for, and the year is in the
# time.
STATIONS_ROWS_SCHEMA = pa.schema(
    [field for field in BY_STATION_SCHEMA if field.name not in ("resolution", "year")]
)

# What a read of one station returns, without the station it was asked for.
STATION_ROWS_SCHEMA = pa.schema(
    [field for field in STATIONS_ROWS_SCHEMA if field.name != "station_code"]
)


class ByStationTable(DeltaWeatherTable):
    """The `by_station` Delta table."""

    def get_key(self, addresser: StationWeatherAddresser) -> S3Key:
        return addresser.get_by_station_key()

    def build_year(self, by_time: ByTimeTable, resolution: str, year: int) -> int:
        """Replace a year's rows of a resolution with what `by_time` now holds, in one commit.
        Returns the number of rows written.

        The year is the UTC year, as the months of `by_time` are. A station that `by_time` no
        longer has rows for in that year loses them here too.
        """
        if not by_time.exists():
            return 0
        months = [f"{year}-{month:02d}" for month in range(1, 13)]
        rows = by_time.dataset().to_table(
            filter=(pc.field("resolution") == resolution) & pc.field("month").isin(months)
        )
        if rows.num_rows == 0:
            return 0
        rows = (
            rows.append_column("year", pa.array([year] * rows.num_rows, pa.int32()))
            .select(BY_STATION_SCHEMA.names)
            # Sorted within each station's file, so one source's rows are together.
            .sort_by(
                [("station_code", "ascending"), ("source", "ascending"), ("timestamp", "ascending")]
            )
        )
        write_deltalake(
            self.table_uri,
            rows,
            mode="overwrite",
            predicate=f"resolution = '{resolution}' AND year = {year}",
            partition_by=PARTITION_COLUMNS,
            storage_options=self.storage_options,
            configuration=TABLE_CONFIGURATION,
            writer_properties=WriterProperties(compression="ZSTD"),
        )
        logger.info(
            "Wrote %d %s rows of %d for %d stations to by_station",
            rows.num_rows,
            resolution,
            year,
            pc.count_distinct(rows["station_code"]).as_py(),
        )
        return rows.num_rows

    def read(
        self, resolution: str, station_code: int, sources: Sequence[str] | None = None
    ) -> pa.Table:
        """Read a station's whole record, sorted by source then time, optionally for some
        sources only. Returns an empty table for a station with no rows, or if the table does
        not exist yet.
        """
        rows = self.read_stations(resolution, [station_code], sources)
        return rows.select(STATION_ROWS_SCHEMA.names).cast(STATION_ROWS_SCHEMA)

    def read_stations(
        self,
        resolution: str,
        station_codes: Sequence[int],
        sources: Sequence[str] | None = None,
        years: Sequence[int] | None = None,
    ) -> pa.Table:
        """Read the record of several stations, sorted by station, source then time, optionally
        for some sources or UTC years only. A station with no rows has none in the result.
        """
        if not self.exists() or not station_codes:
            return STATIONS_ROWS_SCHEMA.empty_table()
        # Only the stations' own files are opened: the table has a file per station per year.
        partitions = [
            ("resolution", "=", resolution),
            ("station_code", "in", [str(code) for code in station_codes]),
        ]
        if years is not None:
            partitions.append(("year", "in", [str(year) for year in years]))
        dataset = self.dataset(partitions=partitions)
        wanted = pc.field("source").isin(list(sources)) if sources is not None else None
        return (
            dataset.to_table(filter=wanted, columns=STATIONS_ROWS_SCHEMA.names)
            .cast(STATIONS_ROWS_SCHEMA)
            .sort_by(
                [("station_code", "ascending"), ("source", "ascending"), ("timestamp", "ascending")]
            )
        )


def build(
    by_station: ByStationTable,
    by_time: ByTimeTable,
    from_year: int,
    current_year: int,
    resolutions: Iterable[str] = (DAILY, HOURLY),
) -> bool:
    """Rebuild every year from `from_year` to the current one. Returns False if a year failed."""
    succeeded = True
    for resolution in resolutions:
        for year in range(from_year, current_year + 1):
            try:
                by_station.build_year(by_time, resolution, year)
            except Exception:
                # One year failing must not stop the others from being rebuilt.
                logger.exception("Failed to rebuild %s %d in by_station", resolution, year)
                succeeded = False
    return succeeded


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    current_year = get_utc_now().year
    parser.add_argument(
        "--from-year",
        type=int,
        default=current_year,
        help="the first year to rebuild; the current year only, if not given",
    )
    args = parser.parse_args()
    configure_logging()
    return 0 if build(ByStationTable(), ByTimeTable(), args.from_year, current_year) else 1


if __name__ == "__main__":
    sys.exit(main())
