import json
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Optional
from urllib.parse import urlencode

from aiohttp import BasicAuth, ClientSession

from wps_wf1.cache_protocol import CacheProtocol
from wps_wf1.query_builders import BuildQuery
from wps_wf1.wfwx_settings import WfwxSettings

logger = logging.getLogger(__name__)

DEFAULT_TTL = 86400


def _cache_key(url: str, params: Dict[str, Any]) -> str:
    """
    Generate a key to use for caching from the provided url and parameter dictionary

    :param url: The URL
    :param params: The key-value pairs to include in the cache key.
    :return: A string representing the derived cache key.
    """
    return f"{url}?{urlencode(params)}"


class WfwxClient:
    def __init__(
        self, session: ClientSession, settings: WfwxSettings, cache: Optional[CacheProtocol] = None
    ):
        self.session = session
        self.settings = settings
        self.cache = cache

    async def _get_json(
        self,
        url: str,
        headers: Dict[str, Any],
        params: Dict[str, Any],
        use_cache: bool = True,
        ttl: int = DEFAULT_TTL,
    ) -> Dict[str, Any]:
        key = _cache_key(url, params)
        if use_cache and self.cache:
            cached = self.cache.get(key)
            if cached:
                return json.loads(cached.decode("utf-8"))

        async with self.session.get(url, headers=headers, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()

        if use_cache and self.cache:
            self.cache.set(key, json.dumps(data).encode("utf-8"), ex=ttl)

        return data

    async def fetch_access_token(self, ttl: int) -> Dict[str, Any]:
        url = self.settings.auth_url
        params = {"user": self.settings.user}
        key = _cache_key(url, params)

        if self.cache:
            cached = self.cache.get(key)
            if cached:
                return json.loads(cached.decode("utf-8"))

        async with self.session.get(
            url, auth=BasicAuth(self.settings.user, self.settings.secret)
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()

        expires = min(data.get("expires_in", ttl), ttl)
        if self.cache:
            self.cache.set(key, json.dumps(data).encode("utf-8"), ex=expires)

        return data

    async def fetch_paged_response_generator(
        self,
        headers: Dict[str, Any],
        query_builder: BuildQuery,
        content_key: str,
        use_cache: bool = False,
        ttl: int = DEFAULT_TTL,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        total_pages = 1
        page_count = 0
        while page_count < total_pages:
            # Build up the request URL.
            url, params = query_builder.query(page_count)
            logger.debug("loading page %d...", page_count)
            data = await self._get_json(url, headers, params, use_cache, ttl)
            total_pages = data.get("page", {}).get("totalPages", 1)
            for obj in data["_embedded"][content_key]:
                yield obj
            page_count += 1

    async def fetch_raw_dailies_for_all_stations(
        self, headers: Dict[str, Any], time_of_interest: datetime
    ) -> list:
        timestamp = int(time_of_interest.timestamp() * 1000)
        params = {
            "query": f"weatherTimestamp=={timestamp}",
            "page": 0,
            "size": self.settings.max_page_size,
        }
        url = f"{self.settings.base_url}/v1/dailies/rsql"

        total_pages = 1
        page_count = 0
        results = []
        while page_count < total_pages:
            p = {**params, "page": page_count}
            async with self.session.get(url, params=p, headers=headers) as resp:
                resp.raise_for_status()
                data = await resp.json()
                total_pages = data["page"]["totalPages"]
                results.extend(data["_embedded"]["dailies"])
            page_count += 1
        return results

    def prepare_fetch_hourlies_query(
        self, raw_station: dict, start_datetime: datetime, end_datetime: datetime
    ):
        start_ts = int(start_datetime.timestamp() * 1000)
        end_ts = int(end_datetime.timestamp() * 1000)
        params = {
            "startTimestamp": start_ts,
            "endTimestamp": end_ts,
            "stationId": raw_station["id"],
        }
        url = f"{self.settings.base_url}/v1/hourlies/search/findHourliesByWeatherTimestampBetweenAndStationIdEqualsOrderByWeatherTimestampAsc"
        return url, params

    async def fetch_hourlies(
        self,
        raw_station: dict,
        headers: Dict[str, Any],
        start_datetime: datetime,
        end_datetime: datetime,
        use_cache: bool,
        ttl: int,
    ) -> dict:
        url, params = self.prepare_fetch_hourlies_query(raw_station, start_datetime, end_datetime)
        return await self._get_json(url, headers, params, use_cache, ttl)

    async def fetch_stations_by_group_id(self, headers: Dict[str, Any], group_id: str) -> dict:
        url = f"{self.settings.base_url}/v1/stationGroups/{group_id}/members"
        async with self.session.get(url, headers=headers) as resp:
            resp.raise_for_status()
            return await resp.json()
        
    async def post_forecasts(self, headers, forecasts_json):
        url = f"{self.settings.base_url}/v1/dailies/daily-bulk"
        async with self.session.post(url, json=forecasts_json, headers=headers) as response:
            response.raise_for_status()
