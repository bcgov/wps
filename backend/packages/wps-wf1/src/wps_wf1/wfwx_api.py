import asyncio
import logging
import math
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional, Tuple

from aiohttp import ClientSession
from wps_shared import config
from wps_shared.db.models.observations import HourlyActual
from wps_shared.schemas.fba import FireCentre
from wps_shared.schemas.forecasts import NoonForecast
from wps_shared.schemas.morecast_v2 import StationDailyFromWF1, WF1PostForecast
from wps_shared.schemas.observations import WeatherStationHourlyReadings
from wps_shared.schemas.stations import (
    DetailedWeatherStationProperties,
    GeoJsonDetailedWeatherStation,
    GeoJsonWeatherStation,
    WeatherStation,
    WeatherStationGeometry,
    WeatherStationProperties,
    WeatherVariables,
    WFWXWeatherStation,
)
from wps_shared.utils.redis import create_redis

from wps_wf1.ecodivisions.ecodivision_seasons import EcodivisionSeasons
from wps_wf1.parsers import (
    WF1RecordTypeEnum,
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
from wps_wf1.query_builders import (
    BuildQuery,
    BuildQueryAllForecastsByAfterStart,
    BuildQueryAllHourliesByRange,
    BuildQueryByStationCode,
    BuildQueryDailiesByStationCode,
    BuildQueryStationGroups,
    BuildQueryStations,
)
from wps_wf1.util import is_station_valid
from wps_wf1.wfwx_client import WfwxClient
from wps_wf1.wfwx_settings import WfwxSettings

logger = logging.getLogger(__name__)


class WfwxApi:
    def __init__(
        self,
        session: ClientSession,
    ):
        self.cache = create_redis()
        self.wfwx_settings = WfwxSettings(
            base_url=config.get("WFWX_BASE_URL"),
            auth_url=config.get("WFWX_AUTH_URL"),
            user=config.get("WFWX_USER"),
            secret=config.get("WFWX_SECRET"),
            auth_cache_expiry=int(config.get("REDIS_AUTH_CACHE_EXPIRY", 600)),
            station_cache_expiry=int(config.get("REDIS_STATION_CACHE_EXPIRY", 604800)),
            hourlies_by_station_code_expiry=int(
                config.get("REDIS_HOURLIES_BY_STATION_CODE_CACHE_EXPIRY", 300)
            ),
            dailies_by_station_code_expiry=int(
                config.get("REDIS_DAILIES_BY_STATION_CODE_CACHE_EXPIRY", 300)
            ),
            use_cache=config.get("REDIS_USE") == "True",
        )
        self.wfwx_client = WfwxClient(session, self.wfwx_settings, self.cache)

    async def _get_auth_header(self) -> dict:
        """Get WFWX auth header"""
        # Fetch access token
        token = await self.wfwx_client.fetch_access_token(self.wfwx_settings.auth_cache_expiry)
        # Construct the header.
        header = {"Authorization": f"Bearer {token['access_token']}"}
        return header

    async def _get_no_cache_auth_header(self) -> dict:
        """Get WFWX auth header with explicit no caching"""
        # Fetch auth header
        header = await self._get_auth_header()
        # Add the cache control header
        header["Cache-Control"] = "no-cache"
        return header

    async def get_stations_by_codes(self, station_codes: List[int]) -> List[WeatherStation]:
        """Get a list of stations by code, from WFWX Fireweather API."""
        logger.info("Using WFWX to retrieve stations by code")
        with EcodivisionSeasons(
            ",".join([str(code) for code in station_codes]), self.cache
        ) as eco_division:
            header = await self._get_auth_header()
            stations = []
            # Iterate through "raw" station data.
            iterator = self.wfwx_client.fetch_paged_response_generator(
                header,
                BuildQueryByStationCode(station_codes),
                "stations",
                use_cache=True,
                ttl=self.wfwx_settings.station_cache_expiry,
            )
            async for raw_station in iterator:
                # If the station is valid, add it to our list of stations.
                if is_station_valid(raw_station):
                    stations.append(parse_station(raw_station, eco_division))
            logger.debug("total stations: %d", len(stations))
            return stations

    async def get_station_data(self, mapper=station_list_mapper, use_no_cache_header: bool = False):
        """Get list of stations from WFWX Fireweather API."""
        logger.info("Using WFWX to retrieve station list")
        if use_no_cache_header:
            header = await self._get_no_cache_auth_header()
        else:
            header = await self._get_auth_header()
        # Iterate through "raw" station data.
        raw_stations = self.wfwx_client.fetch_paged_response_generator(
            header,
            BuildQueryStations(),
            "stations",
            use_cache=True,
            ttl=self.wfwx_settings.station_cache_expiry,
        )
        # Map list of stations into desired shape
        stations = await mapper(raw_stations)
        logger.debug("total stations: %d", len(stations))
        return stations

    async def get_detailed_geojson_stations(
        self, query_builder: BuildQuery
    ) -> Tuple[Dict[int, GeoJsonDetailedWeatherStation], Dict[str, int]]:
        """Fetch and marshall geojson station data"""
        stations = {}
        id_to_code_map = {}
        headers = await self._get_auth_header()
        # Put the stations in a nice dictionary.
        async for raw_station in self.wfwx_client.fetch_paged_response_generator(
            headers, query_builder, "stations", True, self.wfwx_settings.station_cache_expiry
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

    async def get_detailed_stations(self, time_of_interest: datetime):
        """
        We do two things in parallel.
        # 1) list of stations
        # 2) list of noon values
        Once we've collected them all, we merge them into one response
        """

        # Get the authentication header
        header = await self._get_auth_header()
        # Fetch the daily (noon) values for all the stations
        dailies_task = asyncio.create_task(
            self.wfwx_client.fetch_raw_dailies_for_all_stations(header, time_of_interest)
        )
        # Fetch all the stations
        stations_task = asyncio.create_task(
            self.get_detailed_geojson_stations(BuildQueryStations())
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
        self, raw_station, start_timestamp, end_timestamp, eco_division, use_cache, ttl
    ):
        headers = await self._get_auth_header()
        hourlies_json = await self.wfwx_client.fetch_hourlies(
            raw_station, headers, start_timestamp, end_timestamp, use_cache, ttl
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
        self,
        station_codes: List[int],
        start_timestamp: datetime,
        end_timestamp: datetime,
        use_cache: bool = False,
    ) -> List[WeatherStationHourlyReadings]:
        """Get the hourly readings for the list of station codes provided."""
        # Create a list containing all the tasks to run in parallel.
        tasks = []
        # Iterate through "raw" station data.
        headers = await self._get_auth_header()
        iterator = self.wfwx_client.fetch_paged_response_generator(
            headers,
            BuildQueryByStationCode(station_codes),
            "stations",
            True,
            self.wfwx_settings.station_cache_expiry,
        )
        raw_stations = []
        eco_division_key = ""
        # not ideal - we iterate through the stations twice. 1'st time to get the list of station codes,
        # so that we can do an eco division lookup in cache.
        station_codes = set()
        async for raw_station in iterator:
            raw_stations.append(raw_station)
            station_codes.add(raw_station.get("stationCode"))
        eco_division_key = ",".join(str(code) for code in station_codes)
        with EcodivisionSeasons(eco_division_key, self.cache) as eco_division:
            for raw_station in raw_stations:
                task = asyncio.create_task(
                    self.get_hourly_for_station(
                        raw_station,
                        start_timestamp,
                        end_timestamp,
                        eco_division,
                        use_cache,
                        self.wfwx_settings.hourlies_by_station_code_expiry,
                    )
                )
                tasks.append(task)

        # Run the tasks concurrently, waiting for them all to complete.
        return await asyncio.gather(*tasks)

    async def get_noon_forecasts_all_stations(
        self, start_timestamp: datetime
    ) -> List[NoonForecast]:
        """Get the noon forecasts for all stations."""

        noon_forecasts: List[NoonForecast] = []
        headers = await self._get_auth_header()

        # Iterate through "raw" forecast data.
        forecasts_iterator = self.wfwx_client.fetch_paged_response_generator(
            headers,
            BuildQueryAllForecastsByAfterStart(math.floor(start_timestamp.timestamp() * 1000)),
            "dailies",
        )

        forecasts = []
        async for noon_forecast in forecasts_iterator:
            forecasts.append(noon_forecast)

        stations: List[WFWXWeatherStation] = await self.get_station_data(
            mapper=wfwx_station_list_mapper
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
        self, start_timestamp: datetime, end_timestamp: datetime
    ) -> List[HourlyActual]:
        """Get the hourly actuals for all stations."""

        hourly_actuals: List[HourlyActual] = []
        headers = await self._get_auth_header()

        # Iterate through "raw" hourlies data.
        hourlies_iterator = self.wfwx_client.fetch_paged_response_generator(
            headers,
            BuildQueryAllHourliesByRange(
                math.floor(start_timestamp.timestamp() * 1000),
                math.floor(end_timestamp.timestamp() * 1000),
            ),
            "hourlies",
        )

        hourlies = []
        async for hourly in hourlies_iterator:
            hourlies.append(hourly)

        stations: List[WFWXWeatherStation] = await self.get_station_data(
            mapper=wfwx_station_list_mapper
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
        self,
        station_codes: Optional[List[int]],
        fire_centre_station_codes: List[int],
        use_no_cache_header: bool = False,
    ) -> List[WFWXWeatherStation]:
        """Return the WFWX station ids from WFWX API given a list of station codes."""

        # All WFWX stations are requested because WFWX returns a malformed JSON response when too
        # many station codes are added as query parameters.
        # IMPORTANT - the two calls below, cannot be made from within the lambda, as they will be
        # be called multiple times!
        wfwx_stations = await self.get_station_data(
            mapper=wfwx_station_list_mapper, use_no_cache_header=use_no_cache_header
        )

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
        self,
        wfwx_station_ids: List[str],
        start_timestamp: int,
        end_timestamp: int,
    ) -> AsyncGenerator[dict, None]:
        """Get the raw dailies in range for a list of WFWX station ids."""
        headers = await self._get_auth_header()
        return self.wfwx_client.fetch_paged_response_generator(
            headers,
            BuildQueryDailiesByStationCode(start_timestamp, end_timestamp, wfwx_station_ids),
            "dailies",
            True,
            60,
        )

    async def get_dailies_generator(
        self,
        wfwx_stations: List[WFWXWeatherStation],
        time_of_interest: datetime,
        end_time_of_interest: Optional[datetime],
        check_cache: bool = True,
        use_no_cache_header: bool = False,
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
        use_cache = check_cache is True and self.wfwx_settings.use_cache
        logger.info(f"Using cache: {use_cache}")

        if use_no_cache_header:
            headers = await self._get_no_cache_auth_header()
        else:
            headers = await self._get_auth_header()

        dailies_iterator = self.wfwx_client.fetch_paged_response_generator(
            headers,
            BuildQueryDailiesByStationCode(
                timestamp_of_interest, end_timestamp_of_interest, wfwx_station_ids
            ),
            "dailies",
            use_cache=use_cache,
            ttl=self.wfwx_settings.dailies_by_station_code_expiry,
        )

        return dailies_iterator

    async def get_fire_centers(self) -> List[FireCentre]:
        """Get the fire centers from WFWX."""
        wfwx_fire_centers = await self.get_station_data(mapper=fire_center_mapper)
        return list(wfwx_fire_centers.values())

    async def get_dailies_for_stations_and_date(
        self,
        start_time_of_interest: datetime,
        end_time_of_interest: datetime,
        unique_station_codes: List[int],
        fire_centre_station_codes: List[int],
        mapper=dailies_list_mapper,
    ):
        # get station information from the wfwx api
        wfwx_stations = await self.get_wfwx_stations_from_station_codes(
            unique_station_codes, fire_centre_station_codes
        )
        # get the dailies for all the stations
        raw_dailies = await self.get_dailies_generator(
            wfwx_stations, start_time_of_interest, end_time_of_interest
        )

        yesterday_dailies = await mapper(raw_dailies, WF1RecordTypeEnum.ACTUAL)

        return yesterday_dailies

    async def get_forecasts_for_stations_by_date_range(
        self,
        start_time_of_interest: datetime,
        end_time_of_interest: datetime,
        unique_station_codes: List[int],
        fire_centre_station_codes: List[int],
        check_cache=True,
        mapper=dailies_list_mapper,
        use_no_cache_header: bool = False,
    ) -> List[StationDailyFromWF1]:
        # get station information from the wfwx api
        wfwx_stations = await self.get_wfwx_stations_from_station_codes(
            unique_station_codes, fire_centre_station_codes, use_no_cache_header=use_no_cache_header
        )
        # get the daily forecasts for all the stations in the date range
        raw_dailies = await self.get_dailies_generator(
            wfwx_stations=wfwx_stations,
            time_of_interest=start_time_of_interest,
            end_time_of_interest=end_time_of_interest,
            check_cache=check_cache,
            use_no_cache_header=use_no_cache_header,
        )

        forecast_dailies = await mapper(raw_dailies, WF1RecordTypeEnum.FORECAST)

        return forecast_dailies

    async def get_daily_determinates_for_stations_and_date(
        self,
        start_time_of_interest: datetime,
        end_time_of_interest: datetime,
        unique_station_codes: List[int],
        fire_centre_station_codes: List[int],
        mapper=weather_indeterminate_list_mapper,
        check_cache: bool = True,
    ):
        # get station information from the wfwx api
        wfwx_stations = await self.get_wfwx_stations_from_station_codes(
            unique_station_codes, fire_centre_station_codes
        )
        # get the dailies for all the stations
        raw_dailies = await self.get_dailies_generator(
            wfwx_stations, start_time_of_interest, end_time_of_interest, check_cache
        )

        weather_determinates_actuals, weather_determinates_forecasts = await mapper(raw_dailies)

        return weather_determinates_actuals, weather_determinates_forecasts

    async def get_station_groups(self, mapper=weather_station_group_mapper):
        """Get the station groups created by all users from Wild Fire One internal API."""
        header = await self._get_auth_header()
        all_station_groups = self.wfwx_client.fetch_paged_response_generator(
            header, BuildQueryStationGroups(), "stationGroups"
        )
        # Map list of stations into desired shape
        mapped_station_groups = await mapper(all_station_groups)
        logger.debug("total station groups: %d", len(mapped_station_groups))
        return mapped_station_groups

    async def get_stations_by_group_ids(
        self, group_ids: List[str], mapper=unique_weather_stations_mapper
    ):
        """Get all the stations in the specified group from the Wild Fire One internal API."""
        stations_in_groups = []
        headers = await self._get_auth_header()
        for group_id in group_ids:
            stations = await self.wfwx_client.fetch_stations_by_group_id(headers, group_id)
            stations_in_group = mapper(stations)
            stations_in_groups.extend(stations_in_group)
        return stations_in_groups

    async def get_stations_as_geojson(self) -> List[GeoJsonWeatherStation]:
        """Format stations to conform to GeoJson spec"""
        geojson_stations = []
        stations = await self.get_station_data()
        for station in stations:
            geojson_stations.append(
                GeoJsonWeatherStation(
                    properties=WeatherStationProperties(
                        code=station.code,
                        name=station.name,
                        ecodivision_name=station.ecodivision_name,
                        core_season=station.core_season,
                    ),
                    geometry=WeatherStationGeometry(coordinates=[station.long, station.lat]),
                )
            )
        return geojson_stations

    async def post_forecasts(self, forecasts: List[WF1PostForecast]):
        logger.info("Using WFWX to post/put forecasts")
        wfwx_forecast_post_url = f"{self.wfwx_settings.base_url}/v1/dailies/daily-bulk"
        forecasts_json = [forecast.model_dump() for forecast in forecasts]
        headers = await self._get_auth_header()
        await self.wfwx_client.post_forecasts(headers, forecasts_json)

        async with self.wfwx_client.session.post(
            wfwx_forecast_post_url, json=forecasts_json, headers=headers
        ) as response:
            response.raise_for_status()
            logger.info("submitted forecasts to wf1..")


async def get_stations_asynchronously():
    """Get list of stations asynchronously"""
    async with ClientSession() as session:
        wfwx_api = WfwxApi(session)
        return await wfwx_api.get_station_data()


def get_stations_synchronously() -> List[WeatherStation]:
    """Get list of stations - in a synchronous/blocking call."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(get_stations_asynchronously())