"""Hourly reading from weather stations ("actuals")"""

import math
from datetime import datetime, timedelta
from typing import List

from aiohttp.client import ClientSession
from aiohttp.connector import TCPConnector
from wps_shared.wildfire_one.wfwx_api import create_wfwx_api
from wps_wf1.models import WeatherStationHourlyReadings


def get(value: object, condition: bool = True):
    """If the condition is False, or the value is not a number, return None, otherwise
    return the value.
    """
    if not condition or value is None or math.isnan(value):
        return None
    return value


def _get_time_interval(time_of_interest: datetime):
    """Returns the start and end datetimes for hourly readings based on given time of interest"""
    # by default, we want the past 5 days, and if available the next 10 days.
    start_time_stamp = time_of_interest - timedelta(days=5)
    # the UI is interested in hourly reading before and after the time of interest.
    end_time_stamp = time_of_interest + timedelta(days=10)

    return start_time_stamp, end_time_stamp


async def get_hourly_readings(
    station_codes: List[int], time_of_interest: datetime
) -> List[WeatherStationHourlyReadings]:
    """Get the hourly readings for the list of station codes provided.
    Reading 5 days before, and 10 days after the time of interest are returned.
    Depending on configuration, will read from WF1 or from local database.
    """
    start_time_stamp, end_time_stamp = _get_time_interval(time_of_interest)

    # Limit the number of concurrent connections.
    async with ClientSession(connector=TCPConnector(limit=10)) as session:
        wfwx_api = create_wfwx_api(session)
        return await wfwx_api.get_hourly_readings(station_codes, start_time_stamp, end_time_stamp)


async def get_hourly_readings_in_time_interval(
    station_codes: List[int],
    start_time_stamp: datetime,
    end_time_stamp: datetime,
    use_cache: bool = True,
) -> List[WeatherStationHourlyReadings]:
    """Fetch the hourly observations from WFWX API for the list of station codes provided,
    between the start_time_stamp and end_time_stamp specified.
    """
    async with ClientSession(connector=TCPConnector(limit=10)) as session:
        wfwx_api = create_wfwx_api(session)
        return await wfwx_api.get_hourly_readings(
            station_codes, start_time_stamp, end_time_stamp, use_cache
        )
