"""The `stations` dataset: WF1's list of weather stations, as a Delta Lake table in object storage.

The hourly actuals job replaces it with the list it fetches from WF1, so readers such as the
Station Weather API have station names and locations without calling WF1. WF1 lists active,
test and project stations, so a station that has been decommissioned is not in it, though its
history is in `by_time` and `by_station`.

Design: docs/architecture/station-weather-storage.md
"""

import logging
from collections.abc import Iterable
from datetime import datetime

import pyarrow as pa
from deltalake import write_deltalake
from wps_shared.sfms.raster_addresser import S3Key

from wps_weather_data.addresser import StationWeatherAddresser
from wps_weather_data.table import TABLE_CONFIGURATION, DeltaWeatherTable

logger = logging.getLogger(__name__)

STATION_LIST_SCHEMA = pa.schema(
    [
        ("station_code", pa.int32()),
        ("name", pa.string()),
        ("latitude", pa.float64()),
        ("longitude", pa.float64()),
        # Metres above sea level.
        ("elevation", pa.float32()),
        # ACTIVE, TEST or PROJECT.
        ("status", pa.string()),
        ("fetched_at", pa.timestamp("us", tz="UTC")),
    ]
)


def stations_table(raw_stations: Iterable[dict], fetched_at: datetime) -> pa.Table:
    """Rows from WF1's station records, as its API returns them."""
    stations = list(raw_stations)
    return pa.table(
        {
            "station_code": [station["stationCode"] for station in stations],
            "name": [station.get("displayLabel") for station in stations],
            "latitude": [station.get("latitude") for station in stations],
            "longitude": [station.get("longitude") for station in stations],
            "elevation": [station.get("elevation") for station in stations],
            "status": [(station.get("stationStatus") or {}).get("id") for station in stations],
            "fetched_at": [fetched_at] * len(stations),
        },
        schema=STATION_LIST_SCHEMA,
    )


class StationsTable(DeltaWeatherTable):
    """The `stations` Delta table."""

    def get_key(self, addresser: StationWeatherAddresser) -> S3Key:
        return addresser.get_stations_key()

    def replace(self, rows: pa.Table) -> bool:
        """Replace the list with `rows`, in one commit. An empty list is not written, so a WF1
        response with no stations leaves the last list in place. Returns whether it wrote."""
        if rows.num_rows == 0:
            logger.warning("WF1 returned no stations; keeping the stored list")
            return False
        write_deltalake(
            self.table_uri,
            rows.sort_by("station_code"),
            mode="overwrite",
            storage_options=self.storage_options,
            configuration=TABLE_CONFIGURATION,
        )
        logger.info("Wrote %d stations", rows.num_rows)
        return True

    def read(self) -> pa.Table:
        """Every station, by code. Empty if the table does not exist yet."""
        if not self.exists():
            return STATION_LIST_SCHEMA.empty_table()
        return self.dataset().to_table().select(STATION_LIST_SCHEMA.names).sort_by("station_code")
