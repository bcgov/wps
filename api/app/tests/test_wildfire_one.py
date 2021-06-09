""" Unit testing for WFWX API code """
from app.wildfire_one import (BuildQueryAllHourliesByRange, BuildQueryDailesByStationCode)


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
    assert result == ('https://wf1/wfwx/v1/dailies/search/'
                      'findDailiesByStationIdIsInAndWeather'
                      'TimestampBetweenOrderByStationIdAscWeatherTimestampAsc',
                      {
                          'size': '1000',
                          'page': 0,
                          'startingTimestamp': 0,
                          'endingTimestamp': 1,
                          'stationIds': ['1', '2']
                      })
