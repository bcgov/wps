"""This module contains methods for retrieving information from the WFWX Fireweather API."""

import asyncio
import logging
import math
from datetime import datetime
from typing import AsyncGenerator, Dict, Final, List, Optional, Tuple

from aiohttp import ClientSession, TCPConnector
from wps_wf1.query_builders import (
    BuildQuery,
    BuildQueryAllForecastsByAfterStart,
    BuildQueryAllHourliesByRange,
    BuildQueryByStationCode,
    BuildQueryDailiesByStationCode,
    BuildQueryStationGroups,
    BuildQueryStations,
)
from wps_wf1.wfwx_client import WfwxClient
from wps_wf1.wfwx_settings import WfwxSettings

from wps_shared import config
from wps_shared.data.ecodivision_seasons import EcodivisionSeasons
from wps_shared.db.crud.hfi_calc import get_fire_centre_station_codes
from wps_shared.db.crud.stations import _get_noon_date
from wps_shared.db.models.forecasts import NoonForecast
from wps_shared.db.models.observations import HourlyActual
from wps_shared.schemas.fba import FireCentre
from wps_shared.schemas.morecast_v2 import StationDailyFromWF1
from wps_shared.schemas.observations import WeatherStationHourlyReadings
from wps_shared.schemas.stations import (
    DetailedWeatherStationProperties,
    GeoJsonDetailedWeatherStation,
    WeatherStation,
    WeatherStationGeometry,
    WeatherVariables,
)
from wps_shared.utils.redis import create_redis
from wps_shared.wildfire_one.schema_parsers import (
    WF1RecordTypeEnum,
    WFWXWeatherStation,
    dailies_list_mapper,
    fire_center_mapper,
    parse_hourly,
    parse_hourly_actual,
    parse_noon_forecast,
    parse_station,
    station_list_mapper,
    unique_weather_stations_mapper,
    weather_indeterminate_list_mapper,
    weather_station_group_mapper,
    wfwx_station_list_mapper,
)
from wps_shared.wildfire_one.util import is_station_valid

logger = logging.getLogger(__name__)


def create_wps_wf1_client(session: ClientSession):
    wfwx_settings = WfwxSettings(
        base_url=config.get("WFWX_BASE_URL"),
        auth_url=config.get("WFWX_AUTH_URL"),
        user=config.get("WFWX_USER"),
        secret=config.get("WFWX_SECRET"),
    )
    wfwx_client = WfwxClient(session=session, settings=wfwx_settings, cache=create_redis())
    return wfwx_client


async def get_auth_header(session: ClientSession) -> dict:
    """Get WFWX auth header"""
    wfwx_client = create_wps_wf1_client(session)
    # Fetch access token
    token = await wfwx_client.fetch_access_token(int(config.get("REDIS_AUTH_CACHE_EXPIRY", 600)))
    # Construct the header.
    header = {"Authorization": f"Bearer {token['access_token']}"}
    return header


async def get_no_cache_auth_header(session: ClientSession) -> dict:
    """Get WFWX auth header with explicit no caching"""
    # Fetch auth header
    header = await get_auth_header(session)
    # Add the cache control header
    header["Cache-Control"] = "no-cache"
    return header


async def get_stations_by_codes(station_codes: List[int]) -> List[WeatherStation]:
    """Get a list of stations by code, from WFWX Fireweather API."""
    logger.info("Using WFWX to retrieve stations by code")
    with EcodivisionSeasons(",".join([str(code) for code in station_codes])) as eco_division:
        async with ClientSession() as session:
            header = await get_auth_header(session)
            wfwx_client = create_wps_wf1_client(session)
            stations = []
            # 1 week seems a reasonable period to cache stations for.
            redis_station_cache_expiry: Final = int(
                config.get("REDIS_STATION_CACHE_EXPIRY", 604800)
            )
            # Iterate through "raw" station data.
            iterator = wfwx_client.fetch_paged_response_generator(
                header,
                BuildQueryByStationCode(station_codes),
                "stations",
                use_cache=True,
                ttl=redis_station_cache_expiry,
            )
            async for raw_station in iterator:
                # If the station is valid, add it to our list of stations.
                if is_station_valid(raw_station):
                    stations.append(parse_station(raw_station, eco_division))
            logger.debug("total stations: %d", len(stations))
            return stations


async def get_station_data(session: ClientSession, header: dict, mapper=station_list_mapper):
    """Get list of stations from WFWX Fireweather API."""
    logger.info("Using WFWX to retrieve station list")
    wfwx_client = create_wps_wf1_client(session)
    # 1 week seems a reasonable period to cache stations for.
    redis_station_cache_expiry: Final = int(config.get("REDIS_STATION_CACHE_EXPIRY", 604800))
    # Iterate through "raw" station data.
    raw_stations = wfwx_client.fetch_paged_response_generator(
        header,
        BuildQueryStations(),
        "stations",
        use_cache=True,
        ttl=redis_station_cache_expiry,
    )
    # Map list of stations into desired shape
    stations = await mapper(raw_stations)
    logger.debug("total stations: %d", len(stations))
    return stations


async def get_detailed_geojson_stations(
    session: ClientSession, headers: dict, query_builder: BuildQuery
) -> Tuple[Dict[int, GeoJsonDetailedWeatherStation], Dict[str, int]]:
    """Fetch and marshall geojson station data"""
    stations = {}
    id_to_code_map = {}
    # 1 week seems a reasonable period to cache stations for.
    redis_station_cache_expiry: Final = int(config.get("REDIS_STATION_CACHE_EXPIRY", 604800))
    wfwx_client = create_wps_wf1_client(session)
    # Put the stations in a nice dictionary.
    async for raw_station in wfwx_client.fetch_paged_response_generator(
        headers, query_builder, "stations", True, redis_station_cache_expiry
    ):
        station_code = raw_station.get("stationCode")
        station_status = raw_station.get("stationStatus", {}).get("id")
        # Because we can't filter on status in the RSQL, we have to manually exclude stations that are
        # not active.
        if is_station_valid(raw_station):
            id_to_code_map[raw_station.get("id")] = station_code
            geojson_station = GeoJsonDetailedWeatherStation(
                properties=DetailedWeatherStationProperties(
                    code=station_code, name=raw_station.get("displayLabel")
                ),
                geometry=WeatherStationGeometry(
                    coordinates=[raw_station.get("longitude"), raw_station.get("latitude")]
                ),
            )
            stations[station_code] = geojson_station
        else:
            logger.debug("station %s, status %s", station_code, station_status)

    return stations, id_to_code_map


async def get_detailed_stations(time_of_interest: datetime):
    """
    We do two things in parallel.
    # 1) list of stations
    # 2) list of noon values
    Once we've collected them all, we merge them into one response
    """
    # Limit the number of concurrent connections.
    conn = TCPConnector(limit=10)
    async with ClientSession(connector=conn) as session:
        # Get the authentication header
        header = await get_auth_header(session)
        noon_time_of_interest = _get_noon_date(time_of_interest)
        wfwx_client = create_wps_wf1_client(session)
        # Fetch the daily (noon) values for all the stations
        dailies_task = asyncio.create_task(
            wfwx_client.fetch_raw_dailies_for_all_stations(header, noon_time_of_interest)
        )
        # Fetch all the stations
        stations_task = asyncio.create_task(
            get_detailed_geojson_stations(session, header, BuildQueryStations())
        )

        # Await completion of concurrent tasks.
        dailies = await dailies_task
        stations, id_to_code_map = await stations_task

        # Combine dailies and stations
        for daily in dailies:
            station_id = daily.get("stationId")
            station_code = id_to_code_map.get(station_id, None)
            if station_code:
                station = stations[station_code]
                weather_variable = WeatherVariables(
                    temperature=daily.get("temperature"),
                    relative_humidity=daily.get("relativeHumidity"),
                )
                record_type = daily.get("recordType").get("id")
                if record_type in ["ACTUAL", "MANUAL"]:
                    station.properties.observations = weather_variable
                elif record_type == "FORECAST":
                    station.properties.forecasts = weather_variable
                else:
                    logger.info("unexpected record type: %s", record_type)
            else:
                logger.debug("No station found for daily reading (%s)", station_id)

        return list(stations.values())


async def get_hourly_for_station(
    session, header, raw_station, start_timestamp, end_timestamp, eco_division, use_cache, ttl
):
    wfwx_client = create_wps_wf1_client(session)
    hourlies_json = await wfwx_client.fetch_hourlies(
        raw_station, header, start_timestamp, end_timestamp, use_cache, ttl
    )
    hourlies = []
    for hourly in hourlies_json["_embedded"]["hourlies"]:
        # We only accept "ACTUAL" values
        if hourly.get("hourlyMeasurementTypeCode", "").get("id") == "ACTUAL":
            hourlies.append(parse_hourly(hourly))

    return WeatherStationHourlyReadings(
        values=hourlies, station=parse_station(raw_station, eco_division)
    )


async def get_hourly_readings(
    session: ClientSession,
    header: dict,
    station_codes: List[int],
    start_timestamp: datetime,
    end_timestamp: datetime,
    use_cache: bool = False,
) -> List[WeatherStationHourlyReadings]:
    """Get the hourly readings for the list of station codes provided."""
    # Create a list containing all the tasks to run in parallel.
    tasks = []
    # 1 week seems a reasonable period to cache stations for.
    redis_station_cache_expiry: Final = int(config.get("REDIS_STATION_CACHE_EXPIRY", 604800))
    # Iterate through "raw" station data.
    wfwx_client = create_wps_wf1_client(session)
    iterator = wfwx_client.fetch_paged_response_generator(
        header, BuildQueryByStationCode(station_codes), "stations", True, redis_station_cache_expiry
    )
    raw_stations = []
    eco_division_key = ""
    # not ideal - we iterate through the stations twice. 1'st time to get the list of station codes,
    # so that we can do an eco division lookup in redis.
    station_codes = set()
    async for raw_station in iterator:
        raw_stations.append(raw_station)
        station_codes.add(raw_station.get("stationCode"))
    eco_division_key = ",".join(str(code) for code in station_codes)
    cache_expiry_seconds: Final = int(
        config.get("REDIS_HOURLIES_BY_STATION_CODE_CACHE_EXPIRY", 300)
    )
    with EcodivisionSeasons(eco_division_key) as eco_division:
        for raw_station in raw_stations:
            task = asyncio.create_task(
                get_hourly_for_station(
                    session,
                    header,
                    raw_station,
                    start_timestamp,
                    end_timestamp,
                    eco_division,
                    use_cache,
                    cache_expiry_seconds,
                )
            )
            tasks.append(task)

    # Run the tasks concurrently, waiting for them all to complete.
    return await asyncio.gather(*tasks)


async def get_noon_forecasts_all_stations(
    session: ClientSession, header: dict, start_timestamp: datetime
) -> List[NoonForecast]:
    """Get the noon forecasts for all stations."""

    noon_forecasts: List[NoonForecast] = []
    wfwx_client = create_wps_wf1_client(session)

    # Iterate through "raw" forecast data.
    forecasts_iterator = wfwx_client.fetch_paged_response_generator(
        header,
        BuildQueryAllForecastsByAfterStart(math.floor(start_timestamp.timestamp() * 1000)),
        "dailies",
    )

    forecasts = []
    async for noon_forecast in forecasts_iterator:
        forecasts.append(noon_forecast)

    stations: List[WFWXWeatherStation] = await get_station_data(
        session, header, mapper=wfwx_station_list_mapper
    )

    station_code_dict = {station.wfwx_id: station.code for station in stations}

    for noon_forecast in forecasts:
        try:
            station_code = station_code_dict[(noon_forecast["stationId"])]
            parsed_noon_forecast = parse_noon_forecast(station_code, noon_forecast)
            if parsed_noon_forecast is not None:
                noon_forecasts.append(parsed_noon_forecast)
        except KeyError as exception:
            logger.warning("Missing noon forecast for station code", exc_info=exception)

    return noon_forecasts


async def get_hourly_actuals_all_stations(
    session: ClientSession, header: dict, start_timestamp: datetime, end_timestamp: datetime
) -> List[HourlyActual]:
    """Get the hourly actuals for all stations."""

    hourly_actuals: List[HourlyActual] = []
    wfwx_client = create_wps_wf1_client(session)

    # Iterate through "raw" hourlies data.
    hourlies_iterator = wfwx_client.fetch_paged_response_generator(
        header,
        BuildQueryAllHourliesByRange(
            math.floor(start_timestamp.timestamp() * 1000),
            math.floor(end_timestamp.timestamp() * 1000),
        ),
        "hourlies",
    )

    hourlies = []
    async for hourly in hourlies_iterator:
        hourlies.append(hourly)

    stations: List[WFWXWeatherStation] = await get_station_data(
        session, header, mapper=wfwx_station_list_mapper
    )

    station_code_dict = {station.wfwx_id: station.code for station in stations}

    for hourly in hourlies:
        if hourly.get("hourlyMeasurementTypeCode", "").get("id") == "ACTUAL":
            try:
                station_code = station_code_dict[(hourly["stationId"])]
                hourly_actual = parse_hourly_actual(station_code, hourly)
                if hourly_actual is not None:
                    hourly_actuals.append(hourly_actual)
            except KeyError as exception:
                logger.warning("Missing hourly for station code", exc_info=exception)
    return hourly_actuals


async def get_wfwx_stations_from_station_codes(
    session: ClientSession, header, station_codes: Optional[List[int]]
) -> List[WFWXWeatherStation]:
    """Return the WFWX station ids from WFWX API given a list of station codes."""

    # All WFWX stations are requested because WFWX returns a malformed JSON response when too
    # many station codes are added as query parameters.
    # IMPORTANT - the two calls below, cannot be made from within the lambda, as they will be
    # be called multiple times!
    wfwx_stations = await get_station_data(session, header, mapper=wfwx_station_list_mapper)
    # TODO: this is not good. Code in wfwx api shouldn't be filtering on stations codes in hfi....
    fire_centre_station_codes = get_fire_centre_station_codes()

    # Default to all known WFWX station ids if no station codes are specified
    if station_codes is None:
        return list(filter(lambda x: (x.code in fire_centre_station_codes), wfwx_stations))
    requested_stations: List[WFWXWeatherStation] = []
    station_code_dict = {station.code: station for station in wfwx_stations}
    for station_code in station_codes:
        wfwx_station = station_code_dict.get(station_code)
        if wfwx_station is not None:
            requested_stations.append(wfwx_station)
        else:
            logger.error("No WFWX station id for station code: %s", station_code)

    return requested_stations


async def get_raw_dailies_in_range_generator(
    session: ClientSession,
    header: dict,
    wfwx_station_ids: List[str],
    start_timestamp: int,
    end_timestamp: int,
) -> AsyncGenerator[dict, None]:
    """Get the raw dailies in range for a list of WFWX station ids."""
    wfwx_client = create_wps_wf1_client(session)
    return wfwx_client.fetch_paged_response_generator(
        header,
        BuildQueryDailiesByStationCode(start_timestamp, end_timestamp, wfwx_station_ids),
        "dailies",
        True,
        60,
    )


async def get_dailies_generator(
    session: ClientSession,
    header: dict,
    wfwx_stations: List[WFWXWeatherStation],
    time_of_interest: datetime,
    end_time_of_interest: Optional[datetime],
    check_cache: bool = True,
) -> List[dict]:
    """Get the daily actuals/forecasts for the given station ids."""
    # build a list of wfwx station id's
    wfwx_station_ids = [wfwx_station.wfwx_id for wfwx_station in wfwx_stations]

    timestamp_of_interest = math.floor(time_of_interest.timestamp() * 1000)
    if end_time_of_interest is not None:
        end_timestamp_of_interest = math.floor(end_time_of_interest.timestamp() * 1000)
    else:
        end_timestamp_of_interest = timestamp_of_interest

    # for local dev, we can use redis to reduce load in prod, and generally just makes development faster.
    # for production, it's more tricky - we don't want to put too much load on the wf1 api, but we don't
    # want stale values either. We default to 5 minutes, or 300 seconds.
    cache_expiry_seconds: Final = int(config.get("REDIS_DAILIES_BY_STATION_CODE_CACHE_EXPIRY", 300))
    use_cache = check_cache is True and config.get("REDIS_USE") == "True"
    logger.info(f"Using cache: {use_cache}")
    wfwx_client = create_wps_wf1_client(session)

    dailies_iterator = wfwx_client.fetch_paged_response_generator(
        header,
        BuildQueryDailiesByStationCode(
            timestamp_of_interest, end_timestamp_of_interest, wfwx_station_ids
        ),
        "dailies",
        use_cache=use_cache,
        ttl=cache_expiry_seconds,
    )

    return dailies_iterator


async def get_fire_centers(
    session: ClientSession,
    header: dict,
) -> List[FireCentre]:
    """Get the fire centers from WFWX."""
    wfwx_fire_centers = await get_station_data(session, header, mapper=fire_center_mapper)
    return list(wfwx_fire_centers.values())


async def get_dailies_for_stations_and_date(
    session: ClientSession,
    header: dict,
    start_time_of_interest: datetime,
    end_time_of_interest: datetime,
    unique_station_codes: List[int],
    mapper=dailies_list_mapper,
):
    # get station information from the wfwx api
    wfwx_stations = await get_wfwx_stations_from_station_codes(
        session, header, unique_station_codes
    )
    # get the dailies for all the stations
    raw_dailies = await get_dailies_generator(
        session, header, wfwx_stations, start_time_of_interest, end_time_of_interest
    )

    yesterday_dailies = await mapper(raw_dailies, WF1RecordTypeEnum.ACTUAL)

    return yesterday_dailies


async def get_forecasts_for_stations_by_date_range(
    session: ClientSession,
    header: dict,
    start_time_of_interest: datetime,
    end_time_of_interest: datetime,
    unique_station_codes: List[int],
    check_cache=True,
    mapper=dailies_list_mapper,
) -> List[StationDailyFromWF1]:
    # get station information from the wfwx api
    wfwx_stations = await get_wfwx_stations_from_station_codes(
        session, header, unique_station_codes
    )
    # get the daily forecasts for all the stations in the date range
    raw_dailies = await get_dailies_generator(
        session=session,
        header=header,
        wfwx_stations=wfwx_stations,
        time_of_interest=start_time_of_interest,
        end_time_of_interest=end_time_of_interest,
        check_cache=check_cache,
    )

    forecast_dailies = await mapper(raw_dailies, WF1RecordTypeEnum.FORECAST)

    return forecast_dailies


async def get_daily_determinates_for_stations_and_date(
    session: ClientSession,
    header: dict,
    start_time_of_interest: datetime,
    end_time_of_interest: datetime,
    unique_station_codes: List[int],
    mapper=weather_indeterminate_list_mapper,
    check_cache: bool = True,
):
    # get station information from the wfwx api
    wfwx_stations = await get_wfwx_stations_from_station_codes(
        session, header, unique_station_codes
    )
    # get the dailies for all the stations
    raw_dailies = await get_dailies_generator(
        session, header, wfwx_stations, start_time_of_interest, end_time_of_interest, check_cache
    )

    weather_determinates_actuals, weather_determinates_forecasts = await mapper(raw_dailies)

    return weather_determinates_actuals, weather_determinates_forecasts


async def get_station_groups(mapper=weather_station_group_mapper):
    """Get the station groups created by all users from Wild Fire One internal API."""
    async with ClientSession() as session:
        header = await get_auth_header(session)
        wfwx_client = create_wps_wf1_client(session)
        all_station_groups = wfwx_client.fetch_paged_response_generator(
            header, BuildQueryStationGroups(), "stationGroups"
        )
        # Map list of stations into desired shape
        mapped_station_groups = await mapper(all_station_groups)
        logger.debug("total station groups: %d", len(mapped_station_groups))
        return mapped_station_groups


async def get_stations_by_group_ids(group_ids: List[str], mapper=unique_weather_stations_mapper):
    """Get all the stations in the specified group from the Wild Fire One internal API."""
    stations_in_groups = []
    async with ClientSession() as session:
        headers = await get_auth_header(session)
        wfwx_client = create_wps_wf1_client(session)
        for group_id in group_ids:
            stations = await wfwx_client.fetch_stations_by_group_id(headers, group_id)
            stations_in_group = mapper(stations)
            stations_in_groups.extend(stations_in_group)
        return stations_in_groups
