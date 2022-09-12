""" Query builder classes for making requests to WFWX API """
from typing import List, Tuple
from abc import abstractmethod, ABC

from app import config


class BuildQuery(ABC):
    """ Base class for building query urls and params """

    def __init__(self):
        """ Initialize object """
        self.max_page_size = config.get('WFWX_MAX_PAGE_SIZE', 1000)
        self.base_url = config.get('WFWX_BASE_URL')

    @abstractmethod
    def query(self, page) -> Tuple[str, dict]:
        """ Return query url and params """


class BuildQueryStations(BuildQuery):
    """ Class for building a url and RSQL params to request all active stations. """

    def __init__(self):
        """ Prepare filtering on active, test and project stations. """
        super().__init__()
        self.param_query = None
        # In conversation with Dana Hicks, on Apr 20, 2021 - Dana said to show active, test and project.
        for status in ('ACTIVE', 'TEST', 'PROJECT'):
            if self.param_query:
                self.param_query += f',stationStatus.id=="{status}"'
            else:
                self.param_query = f'stationStatus.id=="{status}"'

    def query(self, page) -> Tuple[str, dict]:
        """ Return query url and params with rsql query for all weather stations marked active. """
        params = {'size': self.max_page_size, 'sort': 'displayLabel',
                  'page': page, 'query': self.param_query}
        url = f'{self.base_url}/v1/stations'
        return url, params


class BuildQueryByStationCode(BuildQuery):
    """ Class for building a url and params to request a list of stations by code """

    def __init__(self, station_codes: List[int]):
        """ Initialize object """
        super().__init__()
        self.querystring = ''
        for code in station_codes:
            if len(self.querystring) > 0:
                self.querystring += ' or '
            self.querystring += f'stationCode=={code}'

    def query(self, page) -> Tuple[str, dict]:
        """ Return query url and params for a list of stations """
        params = {'size': self.max_page_size,
                  'sort': 'displayLabel', 'page': page, 'query': self.querystring}
        url = f'{self.base_url}/v1/stations/rsql'
        return url, params


class BuildQueryAllHourliesByRange(BuildQuery):
    """ Builds query for requesting all hourlies in a time range"""

    def __init__(self, start_timestamp: int, end_timestamp: int):
        """ Initialize object """
        super().__init__()
        self.querystring: str = "weatherTimestamp >=" + \
            str(start_timestamp) + ";" + "weatherTimestamp <" + str(end_timestamp)

    def query(self, page) -> Tuple[str, dict]:
        """ Return query url for hourlies between start_timestamp, end_timestamp"""
        params = {'size': self.max_page_size, 'page': page, 'query': self.querystring}
        url = f'{self.base_url}/v1/hourlies/rsql'
        return url, params


class BuildQueryAllForecastsByAfterStart(BuildQuery):
    """ Builds query for requesting all dailies in a time range"""

    def __init__(self, start_timestamp: int):
        """ Initialize object """
        super().__init__()
        self.querystring = f"weatherTimestamp >={start_timestamp};recordType.id == 'FORECAST'"

    def query(self, page) -> Tuple[str, dict]:
        """ Return query url for dailies between start_timestamp, end_timestamp"""
        params = {'size': self.max_page_size, 'page': page, 'query': self.querystring}
        url = f'{self.base_url}/v1/dailies/rsql'
        return url, params


class BuildQueryDailiesByStationCode(BuildQuery):
    """ Builds query for requesting dailies in a time range for the station codes"""

    def __init__(self, start_timestamp: int, end_timestamp: int, station_ids: List[str]):
        """ Initialize object """
        super().__init__()
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.station_ids = station_ids

    def query(self, page) -> Tuple[str, dict]:
        """ Return query url for dailies between start_timestamp, end_timestamp"""
        params = {'size': self.max_page_size,
                  'page': page,
                  'startingTimestamp': self.start_timestamp,
                  'endingTimestamp': self.end_timestamp,
                  'stationIds': self.station_ids}
        url = (f'{self.base_url}/v1/dailies/search/findDailiesByStationIdIsInAndWeather' +
               'TimestampBetweenOrderByStationIdAscWeatherTimestampAsc')
        return url, params
