""" Unit testing for WFWX API code """
import asyncio
from pytest_mock import MockFixture
from app.wildfire_one import (BuildQueryAllHourliesByRange,
                              BuildQueryDailesByStationCode,
                              WFWXWeatherStation,
                              get_wfwx_stations_from_station_codes)


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


def test_build_dailies_by_station_code():
    """ Verifies the query builder returns the correct url and parameters for dailies by station code """
    query_builder = BuildQueryDailesByStationCode(0, 1, ['1', '2'])
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


code1 = 322
code2 = 239
all_station_codes = [code1, code2]
station_1 = WFWXWeatherStation(code=code1, wfwx_id="one")
station_2 = WFWXWeatherStation(code=code2, wfwx_id="two")
all_stations = [station_1, station_2]


@asyncio.coroutine
def mock_get_stations(_, __, **___):
    """ Returns mocked WFWXWeatherStations. """
    return all_stations


@asyncio.coroutine
def mock_get_fire_centre_station_codes(__):
    """ Returns mocked WFWXWeatherStations codes. """
    return all_station_codes


def test_get_ids_from_station_codes_no_stations(mocker: MockFixture, mock_session):
    """ Verifies the query builder returns the correct url and parameters for dailies by station code """
    mocker.patch('app.utils.hfi_calculator.get_all_stations', mock_get_fire_centre_station_codes)
    mocker.patch('app.wildfire_one.get_stations', mock_get_stations)

    async def run_test():
        """ Async function to run test and assert result """
        result = await get_wfwx_stations_from_station_codes(None, {}, None)
        assert result == []

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_test())


def test_get_ids_from_station_codes(mocker: MockFixture, mock_session):
    """ Verifies the query builder returns the correct url and parameters for dailies by station code """
    mocker.patch('app.utils.hfi_calculator.get_all_stations', mock_get_fire_centre_station_codes)
    mocker.patch('app.wildfire_one.get_stations', mock_get_stations)

    async def run_test():
        """ Async function to run test and assert result """
        result = await get_wfwx_stations_from_station_codes(None, {}, [code1])
        assert result == [station_1]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_test())
