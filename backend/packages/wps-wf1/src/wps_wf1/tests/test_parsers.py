

from datetime import datetime, timezone
import math
from wps_wf1.models import HourlyActual
from wps_wf1.parsers import parse_hourly_actual


class TestParseHourlyActual:
    def test_parse_hourly_actual(self):
        """ Valid fields are set when values exist """
        raw_actual = {
            "weatherTimestamp": datetime.now(tz=timezone.utc).timestamp(),
            "temperature": 0.0,
            "relativeHumidity": 0.0,
            "windSpeed": 0.0,
            "windDirection": 0.0,
            "precipitation": 0.0,
            "fineFuelMoistureCode": 0.0,
            "initialSpreadIndex": 0.0,
            "fireWeatherIndex": 0.0
        }

        hourly_actual = parse_hourly_actual(1, raw_actual)
        assert isinstance(hourly_actual, HourlyActual)
        assert hourly_actual.rh_valid is True
        assert hourly_actual.temp_valid is True
        assert hourly_actual.wdir_valid is True
        assert hourly_actual.precip_valid is True
        assert hourly_actual.wspeed_valid is True


    def test_invalid_metrics(self):
        """ Metric valid flags should be false """

        raw_actual = {
            "weatherTimestamp": datetime.now(tz=timezone.utc).timestamp(),
            "temperature": 0.0,
            "relativeHumidity": 101,
            "windSpeed": -1,
            "windDirection": 361,
            "precipitation": -1,
            "fineFuelMoistureCode": 0.0,
            "initialSpreadIndex": 0.0,
            "fireWeatherIndex": 0.0
        }

        hourly_actual = parse_hourly_actual(1, raw_actual)
        assert isinstance(hourly_actual, HourlyActual)
        assert hourly_actual.temp_valid is True
        assert hourly_actual.rh_valid is False
        assert hourly_actual.precip_valid is False
        assert hourly_actual.wspeed_valid is False
        assert hourly_actual.wdir_valid is False


    def test_invalid_metrics_from_wfwx(self):
        """ Metric valid flags should be false """

        raw_actual = {
            "weatherTimestamp": datetime.now(tz=timezone.utc).timestamp(),
            "temperature": 0.0,
            "relativeHumidity": 101,
            "windSpeed": -1,
            "windDirection": 361,
            "fineFuelMoistureCode": 0.0,
            "initialSpreadIndex": 0.0,
            "fireWeatherIndex": 0.0,
            "observationValid": False,
            "observationValidComment": "Precipitation can not be null."
        }

        hourly_actual = parse_hourly_actual(1, raw_actual)
        assert isinstance(hourly_actual, HourlyActual)
        assert hourly_actual.temp_valid is True
        assert hourly_actual.rh_valid is False
        assert hourly_actual.precip_valid is False
        assert hourly_actual.wspeed_valid is False
        assert hourly_actual.wdir_valid is False
        assert hourly_actual.precipitation == math.nan
