""" Unit tests for API - forecasts.
"""
import json
import logging
from datetime import datetime
import numpy
from starlette.testclient import TestClient
from asynctest import patch, TestCase

from main import APP
import tests.common

LOGGER = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class ResponseAsyncContextManager(tests.common.ResponseAsyncContextManagerBase):
    """ Stubbed asyncronous context manager.
    """

    async def __aenter__(self):
        """ Enter context """
        if 'page' in self.url:
            with open('tests/wf1_stations_by_code.json') as page:
                return tests.common.ClientResponse(json_response=json.load(page))
        if 'spotwx' in self.url:
            with open('tests/spotwx_response_sample.csv', mode='r') as spotwx:
                data = spotwx.read()
                return tests.common.ClientResponse(text_response=data)
        return await super().__aenter__()


class ForecastTestCase(TestCase):
    """ Tests relating to /forecasts (not using WFWX) """

    @staticmethod
    def use_wfwx():
        """ Don't use wfwx in API calls. """
        return 'False'

    @classmethod
    def setUpClass(cls):
        with patch('wildfire_one.ClientSession.get') as mock_get:
            with patch('config.getenv') as mock_getenv:

                def getenv_side_effect(key):
                    """ Override of getenv to ensure we're using wildfire API.
                    """
                    environment = {
                        'SPOTWX_API_KEY': 'something',
                        'SPOTWX_BASE_URI': 'spotwx',
                        'USE_WFWX': cls.use_wfwx(),
                        'WFWX_USER': 'user',
                        'WFWX_SECRET': 'secret',
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
                cls.response = client.post('/forecasts/', headers={'Content-Type': 'application/json'},
                                           json={"stations": [
                                               "331",
                                               "328"
                                           ]})
                cls.response_json = cls.response.json()

                mock_get.assert_called()
                mock_getenv.assert_called()

    def test_ok(self):
        """ We expect a 200 ok response. """
        self.assertEqual(self.response.status_code, 200)

    def test_num_forecasts(self):
        """ We asked for forecasts from two stations, we expect forecasts from two stations. """
        self.assertEqual(len(self.response_json['forecasts']), 2)

    def test_10_day_forecast(self):
        """ We're expecting a 10 day forecast. """
        self.assertEqual(len(self.response_json['forecasts'][0]['values']), 10)

    def test_noon_values_only(self):
        """ We're expecting noon values (20h00 UTC). """
        for forecast in self.response_json['forecasts']:
            for values in forecast['values']:
                timestamp = datetime.fromisoformat(values['datetime'])
                self.assertEqual(timestamp.hour, 20)

    def test_temperature_value(self):
        """ We're expecting interpolated values, so we check on of the calculations. """
        # dates matching csv file:
        x_p = [datetime.fromisoformat('2020-05-04T18:00:00').timestamp(),
               datetime.fromisoformat('2020-05-04T21:00:00').timestamp()]
        # temperatures matching csv file:
        f_p = [8.7, 12.1]
        # calculate interpolated temperature
        expected_temperature = numpy.interp(datetime.fromisoformat(
            '2020-05-04T20:00:00').timestamp(), x_p, f_p)
        self.assertEqual(
            self.response_json['forecasts'][0]['values'][0]['temperature'], expected_temperature)


class ForecastTestCaseUseFwWx(ForecastTestCase):
    """ Tests relating to /forecasts (using WFWX) """

    @staticmethod
    def use_wfwx():
        """ Don't use WFWX API in tests """
        return 'True'
