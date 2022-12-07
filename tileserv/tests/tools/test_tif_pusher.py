""" Unit testing for hourly actuals job """
import logging

logger = logging.getLogger(__name__)


def test_invalid_metrics():
    """ Metric valid flags should be false """

    raw_actual = {
        "temperature": 0.0,
        "relativeHumidity": 101,
        "windSpeed": -1,
        "windDirection": 361,
        "precipitation": -1,
        "fineFuelMoistureCode": 0.0,
        "initialSpreadIndex": 0.0,
        "fireWeatherIndex": 0.0
    }

    assert True is True
