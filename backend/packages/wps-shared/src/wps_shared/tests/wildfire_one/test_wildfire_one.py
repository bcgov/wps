"""Unit testing for WFWX API code"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
import wps_shared.wildfire_one.wfwx_post_api
from fastapi import HTTPException
from pytest_mock import MockFixture
from wps_shared.wildfire_one.wfwx_api import (
    WFWXWeatherStation,
    get_wfwx_stations_from_station_codes,
)
from wps_shared.wildfire_one.wfwx_post_api import post_forecasts

code1 = 322
code2 = 239
all_station_codes = [{"station_code": code1}, {"station_code": code2}]
station_1 = WFWXWeatherStation(
    code=code1, name="name", wfwx_id="one", latitude=0, longitude=0, elevation=0, zone_code="T1"
)
station_2 = WFWXWeatherStation(
    code=code2, name="name", wfwx_id="two", latitude=0, longitude=0, elevation=0, zone_code="T1"
)
all_stations = [station_1, station_2]


@pytest.fixture()
def mock_responses(mocker: MockFixture):
    """Mocks out hourly actuals as async result"""

    async def mock_get_stations(_, __, **___):
        """Returns mocked WFWXWeatherStations."""
        return all_stations

    def mock_get_fire_centre_station_codes(__):
        """Returns mocked WFWXWeatherStations codes."""
        return all_station_codes

    mocker.patch("wps_shared.db.crud.hfi_calc.get_all_stations", mock_get_fire_centre_station_codes)
    mocker.patch("wps_shared.wildfire_one.wfwx_api.get_station_data", mock_get_stations)


def test_get_ids_from_station_codes_no_stations(mock_responses):
    """Verifies the query builder returns the correct url and parameters for dailies by station code"""

    async def run_test():
        """Async function to run test and assert result"""
        result = await get_wfwx_stations_from_station_codes(None, {}, None)
        assert len(result) == 2

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_test())


def test_get_ids_from_station_codes(mock_responses):
    """Verifies the query builder returns the correct url and parameters for dailies by station code"""

    async def run_test():
        """Async function to run test and assert result"""
        result = await get_wfwx_stations_from_station_codes(None, {}, [code1])
        assert result == [station_1]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_test())


@pytest.mark.anyio
@patch("wps_shared.wildfire_one.wfwx_post_api.ClientSession")
async def test_wf1_post_failure(mock_client, monkeypatch: pytest.MonkeyPatch):
    """Verifies that posting to WF1 raises an exception upon failure"""

    async def mock_get_auth_header(_):
        return {}

    monkeypatch.setattr(
        wps_shared.wildfire_one.wfwx_post_api, "get_auth_header", mock_get_auth_header
    )
    mock_client.post.return_value.__aenter__.return_value = AsyncMock(status=400)
    with pytest.raises(HTTPException):
        await post_forecasts(mock_client, [])
