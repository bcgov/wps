"""This module contains methods for retrieving information from the WFWX Fireweather API."""

import logging

from aiohttp import ClientSession
from wps_wf1.wfwx_api import WfwxApi
from wps_wf1.wfwx_client import WfwxClient
from wps_wf1.wfwx_settings import WfwxSettings

from wps_shared import config
from wps_shared.utils.redis import create_redis

logger = logging.getLogger(__name__)

def create_wfwx_api(session: ClientSession) -> WfwxApi:
    wfwx_settings = WfwxSettings(
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
    wfwx_api = WfwxApi(session=session, wfwx_settings=wfwx_settings, cache=create_redis())
    return wfwx_api
