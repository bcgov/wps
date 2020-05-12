""" Unit tests for API.
"""
import logging
from datetime import datetime
import numpy
import nest_asyncio
from starlette.testclient import TestClient
from asynctest import CoroutineMock, patch, TestCase

from main import APP

LOGGER = logging.getLogger(__name__)

# We need to allow for nesting of asyncio, since both our unit test and our api have event loops.
nest_asyncio.apply()


class ForecastTestCase(TestCase):
    """ Tests relating to /forecasts """

    @patch('forecasts.ClientSession.get')
    # pylint: disable=invalid-overridden-method
    # pylint: disable=arguments-differ
    async def setUp(self, mock_get):
        with open('tests/spotwx_response_sample.csv', mode='r') as spotwx:
            data = spotwx.read()
            mock_get.return_value.__aenter__.return_value.text = CoroutineMock(
                return_value=data)

        client = TestClient(APP)
        self.response = client.post('/forecasts/', headers={'Content-Type': 'application/json'},
                                    json={"stations": [
                                        "331",
                                        "328"
                                    ]})
        self.response_json = self.response.json()

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
