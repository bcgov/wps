""" Unit testing for WFWX API code """
import asyncio
from unittest.mock import patch, AsyncMock
import pytest
from fastapi import HTTPException
from pytest_mock import MockFixture

from app.wildfire_one.query_builders import (BuildQueryAllForecastsByAfterStart,
                                             BuildQueryAllHourliesByRange,
                                             BuildQueryDailiesByStationCode,
                                             BuildQueryStationGroups)
from app.wildfire_one.wfwx_api import (WFWXWeatherStation,
                                       get_wfwx_stations_from_station_codes)
from app.wildfire_one.wfwx_post_api import post_forecasts


def test_build_all_hourlies_query():
    """ Verifies the query builder returns the correct url and parameters """
    query_builder = BuildQueryAllHourliesByRange(0, 1)
    result = query_builder.query(0)
    assert result == ("https://wf1/wfwx/v1/hourlies/rsql",
                      {
                          'size': '1000',
                          'page': 0,
                          'query': 'weatherTimestamp >=0;weatherTimestamp <1'
                      })


def test_build_forecasts_query():
    """ Verifies the query builder returns the correct url and parameters """
    query_builder = BuildQueryAllForecastsByAfterStart(0)
    result = query_builder.query(0)
    assert result == ("https://wf1/wfwx/v1/dailies/rsql",
                      {
                          'size': '1000',
                          'page': 0,
                          'query': "weatherTimestamp >=0;recordType.id == 'FORECAST'"
                      })


def test_build_dailies_by_station_code():
    """ Verifies the query builder returns the correct url and parameters for dailies by station code """
    query_builder = BuildQueryDailiesByStationCode(0, 1, ['1', '2'])
    result = query_builder.query(0)
    assert result == ('https://wf1/wfwx/v1/dailies/search/' +
                      'findDailiesByStationIdIsInAndWeather' +
                      'TimestampBetweenOrderByStationIdAscWeatherTimestampAsc',
                      {
                          'size': '1000',
                          'page': 0,
                          'startingTimestamp': 0,
                          'endingTimestamp': 1,
                          'stationIds': ['1', '2']
                      })


def test_build_station_groups_query():
    """ Verifies the query builder returns the correct url and parameters for a station groups query"""
    query_builder = BuildQueryStationGroups()
    result = query_builder.query(0)
    assert result == ('https://wf1/wfwx/v1/stationGroups',
                      {
                          'size': '1000',
                          'page': 0,
                          'sort': 'groupOwnerUserId,asc'
                      })


code1 = 322
code2 = 239
all_station_codes = [{'station_code': code1}, {'station_code': code2}]
station_1 = WFWXWeatherStation(code=code1, name="name", wfwx_id="one",
                               latitude=0, longitude=0, elevation=0, zone_code='T1')
station_2 = WFWXWeatherStation(code=code2, name="name", wfwx_id="two",
                               latitude=0, longitude=0, elevation=0, zone_code='T1')
all_stations = [station_1, station_2]


@pytest.fixture()
def mock_responses(mocker: MockFixture):
    """ Mocks out hourly actuals as async result """
    async def mock_get_stations(_, __, **___):
        """ Returns mocked WFWXWeatherStations. """
        return all_stations

    def mock_get_fire_centre_station_codes(__):
        """ Returns mocked WFWXWeatherStations codes. """
        return all_station_codes

    mocker.patch('app.db.crud.hfi_calc.get_all_stations', mock_get_fire_centre_station_codes)
    mocker.patch('app.wildfire_one.wfwx_api.get_station_data', mock_get_stations)


def test_get_ids_from_station_codes_no_stations(mock_responses):
    """ Verifies the query builder returns the correct url and parameters for dailies by station code """
    async def run_test():
        """ Async function to run test and assert result """
        result = await get_wfwx_stations_from_station_codes(None, {}, None)
        assert len(result) == 2

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_test())


def test_get_ids_from_station_codes(mock_responses):
    """ Verifies the query builder returns the correct url and parameters for dailies by station code """

    async def run_test():
        """ Async function to run test and assert result """
        result = await get_wfwx_stations_from_station_codes(None, {}, [code1])
        assert result == [station_1]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_test())


@pytest.mark.anyio
@patch('app.wildfire_one.wfwx_post_api.ClientSession')
async def test_wf1_post_failure(mock_client):
    """ Verifies that posting to WF1 raises an exception upon failure """
    mock_client.post.return_value.__aenter__.return_value = AsyncMock(status=400)
    with pytest.raises(HTTPException):
        await post_forecasts(mock_client, 'token', [])
