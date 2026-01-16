"""
Common utilities for SFMS jobs.
"""

import logging
from datetime import datetime
from typing import List
from aiohttp import ClientSession
from wps_shared.schemas.sfms import SFMSDailyActual
from wps_shared.wildfire_one.wildfire_fetchers import fetch_raw_dailies_for_all_stations
from wps_shared.wildfire_one.util import is_station_valid
from wps_shared.schemas.stations import WeatherStation

logger = logging.getLogger(__name__)


async def fetch_station_actuals(
    session: ClientSession,
    headers: dict,
    time_of_interest: datetime,
    stations: List[WeatherStation],
    require_elevation: bool = False,
) -> List[SFMSDailyActual]:
    logger.info("Fetching station %s for", time_of_interest)

    station_lookup = {station.code: station for station in stations}
    raw_dailies = await fetch_raw_dailies_for_all_stations(session, headers, time_of_interest)

    records = []
    for raw_daily in raw_dailies:
        try:
            station_data = raw_daily.get("stationData")
            if not is_station_valid(station_data):
                continue

            station_code = station_data.get("stationCode")
            record_type = raw_daily.get("recordType", {}).get("id")

            if record_type != "ACTUAL":
                continue

            if station_code not in station_lookup:
                logger.debug("Station %s not found in station lookup", station_code)
                continue

            station = station_lookup[station_code]

            if require_elevation and station.elevation is None:
                logger.warning("No elevation data for station %s, skipping", station_code)
                continue

            actual = SFMSDailyActual(
                code=station_code,
                lat=station.lat,
                lon=station.long,
                elevation=station.elevation,
                temperature=raw_daily.get("temperature"),
                relative_humidity=raw_daily.get("relativeHumidity"),
                precipitation=raw_daily.get("precipitation"),
                wind_speed=raw_daily.get("windSpeed"),
            )
            records.append(actual)

        except Exception as e:
            logger.error("Error processing daily for station: %s", e, exc_info=True)
            continue

    logger.info("Found %d stations with valid data", len(records))
    return records
