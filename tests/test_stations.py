""" Unit tests for API - stations using wf1
"""
import json
import logging
from asynctest import patch, TestCase
from starlette.testclient import TestClient

from main import APP
import tests.common

LOGGER = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class ResponseAsyncContextManager(tests.common.ResponseAsyncContextManagerBase):
    """ Stubbed asyncronous context manager.
    """
    async def __aenter__(self):
        """ Enter context - return the appropriate response object depending on the url
        """
        if 'page' in self.url:
            match = self.url.find('page=')
            with open('tests/wf1_stations_page{}.json'.format(self.url[match+5:match+6])) as page:
                return tests.common.ClientResponse(json_response=json.load(page))
        return await super().__aenter__()


class StationsTestCase(TestCase):
    """ Tests relating to stations """

    @classmethod
    def setUpClass(cls):
        """ Make a call to that /stations/ endpoint using a stubbed out ClientSession
        """
        with patch('forecasts.ClientSession.get') as mock_get:
            with patch('config.getenv') as mock_getenv:

                def getenv_side_effect(key):
                    """ Override of getenv to ensure we're using wildfire API.
                    """
                    environment = {
                        'USE_WFWX': 'True',
                        'WFWX_USER': 'user',
                        'WFWX_SECRET': 'secret',
                        'ORIGINS': 'secret',
                        'WFWX_AUTH_URL': 'http://localhost/token',
                        'WFWX_BASE_URL': 'http://localhost/page',
                        'WFWX_MAX_PAGE_SIZE': 1000
                    }
                    return environment.get(key, None)

                mock_getenv.side_effect = getenv_side_effect

                # pylint: disable=unused-argument
                def get_side_effect(url, **args):
                    return ResponseAsyncContextManager(url)

                mock_get.side_effect = get_side_effect

                client = TestClient(APP)
                cls.response = client.get('/stations/')
                cls.response_json = cls.response.json()

                mock_get.assert_called()
                mock_getenv.assert_called()

    def test_station_number(self):
        """ We expect there to be 16 weather stations. Even though we were given 50 stations from the
        API, some of those stations are inactive/invalid/disabled or don't have lat/long.
        """
        self.assertEqual(len(self.response_json['weather_stations']), 16)

    def test_station_serialization(self):
        """ We expect a station to have a code, name, lat and long. """
        actual_station = self.response_json['weather_stations'][0]
        self.assertEqual(actual_station, {'code': 67, 'name': 'HAIG CAMP',
                                          'lat': 49.3806, 'long': -121.525967})
