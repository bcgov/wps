import math
from datetime import datetime, timezone

import pytest
from pytest import approx
from wps_shared.db.models.observations import HourlyActual
from wps_shared.schemas.sfms import SFMSDailyActual
from wps_wf1.parsers import (
    parse_hourly_actual,
    sfms_daily_actuals_mapper,
    sfms_daily_forecasts_mapper,
)


def _make_raw_daily(
    station_code,
    record_type="ACTUAL",
    status="ACTIVE",
    lat=49.0,
    lon=-123.0,
    elevation=100,
    site_type="WXSTN_TEL",
    **weather_fields,
):
    defaults = {
        "temperature": None,
        "relativeHumidity": None,
        "precipitation": None,
        "windSpeed": None,
        "windDirection": None,
    }
    defaults.update(weather_fields)
    return {
        "stationData": {
            "stationCode": station_code,
            "stationStatus": {"id": status},
            "siteType": {"id": site_type},
            "latitude": lat,
            "longitude": lon,
            "elevation": elevation,
        },
        "recordType": {"id": record_type},
        **defaults,
    }


class TestParseHourlyActual:
    def test_parse_hourly_actual(self):
        """Valid fields are set when values exist"""
        raw_actual = {
            "weatherTimestamp": datetime.now(tz=timezone.utc).timestamp(),
            "temperature": 0.0,
            "relativeHumidity": 0.0,
            "windSpeed": 0.0,
            "windDirection": 0.0,
            "precipitation": 0.0,
            "fineFuelMoistureCode": 0.0,
            "initialSpreadIndex": 0.0,
            "fireWeatherIndex": 0.0,
        }

        hourly_actual = parse_hourly_actual(1, raw_actual)
        assert isinstance(hourly_actual, HourlyActual)
        assert hourly_actual.rh_valid is True
        assert hourly_actual.temp_valid is True
        assert hourly_actual.wdir_valid is True
        assert hourly_actual.precip_valid is True
        assert hourly_actual.wspeed_valid is True

    def test_invalid_metrics(self):
        """Metric valid flags should be false"""

        raw_actual = {
            "weatherTimestamp": datetime.now(tz=timezone.utc).timestamp(),
            "temperature": 0.0,
            "relativeHumidity": 101,
            "windSpeed": -1,
            "windDirection": 361,
            "precipitation": -1,
            "fineFuelMoistureCode": 0.0,
            "initialSpreadIndex": 0.0,
            "fireWeatherIndex": 0.0,
        }

        hourly_actual = parse_hourly_actual(1, raw_actual)
        assert isinstance(hourly_actual, HourlyActual)
        assert hourly_actual.temp_valid is True
        assert hourly_actual.rh_valid is False
        assert hourly_actual.precip_valid is False
        assert hourly_actual.wspeed_valid is False
        assert hourly_actual.wdir_valid is False

    def test_invalid_metrics_from_wfwx(self):
        """Metric valid flags should be false"""

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
            "observationValidComment": "Precipitation can not be null.",
        }

        hourly_actual = parse_hourly_actual(1, raw_actual)
        assert isinstance(hourly_actual, HourlyActual)
        assert hourly_actual.temp_valid is True
        assert hourly_actual.rh_valid is False
        assert hourly_actual.precip_valid is False
        assert hourly_actual.wspeed_valid is False
        assert hourly_actual.wdir_valid is False
        assert hourly_actual.precipitation is math.nan


class TestSfmsDailyActualsMapper:
    def test_maps_actual_with_all_weather_fields(self):
        raw = _make_raw_daily(
            100,
            elevation=150,
            temperature=15.0,
            relativeHumidity=50.0,
            precipitation=2.5,
            windSpeed=10.0,
            windDirection=180.0,
            fineFuelMoistureCode=85.0,
            duffMoistureCode=30.0,
            droughtCode=200.0,
        )

        result = sfms_daily_actuals_mapper([raw])

        assert len(result) == 1
        assert result[0] == SFMSDailyActual(
            code=100,
            lat=49.0,
            lon=-123.0,
            elevation=150,
            temperature=15.0,
            relative_humidity=50.0,
            precipitation=2.5,
            wind_speed=10.0,
            wind_direction=180.0,
            ffmc=85.0,
            dmc=30.0,
            dc=200.0,
        )

    def test_maps_none_weather_fields(self):
        raw = _make_raw_daily(100)

        result = sfms_daily_actuals_mapper([raw])

        assert len(result) == 1
        actual = result[0]
        assert actual.temperature is None
        assert actual.relative_humidity is None
        assert actual.precipitation is None
        assert actual.wind_speed is None
        assert actual.wind_direction is None
        assert actual.ffmc is None
        assert actual.dmc is None
        assert actual.dc is None

    def test_maps_manual_record_type_as_actual(self):
        station = _make_station(100, lat=49.0, lon=-123.0, elevation=150)
        raw = _make_raw_daily(100, record_type="MANUAL", temperature=15.0)

        result = sfms_daily_actuals_mapper([raw], [station])

        assert len(result) == 1
        assert result[0].code == 100
        assert result[0].temperature == approx(15.0)

    def test_filters_forecast_record_type(self):
        raw = _make_raw_daily(100, record_type="FORECAST", temperature=20.0)

        assert sfms_daily_actuals_mapper([raw]) == []

    def test_filters_inactive_station(self):
        raw = _make_raw_daily(100, status="INACTIVE", temperature=20.0)

        assert sfms_daily_actuals_mapper([raw]) == []

    @pytest.mark.parametrize("status", ["TEST", "PROJECT"])
    def test_filters_non_active_station(self, status):
        raw = _make_raw_daily(100, status=status, temperature=20.0)

        assert sfms_daily_actuals_mapper([raw]) == []

    def test_filters_invalid_site_type(self):
        raw = _make_raw_daily(100, site_type="UNKNOWN_TYPE", temperature=20.0)

        assert sfms_daily_actuals_mapper([raw]) == []

    def test_filters_missing_site_type(self):
        raw = _make_raw_daily(100, temperature=20.0)
        del raw["stationData"]["siteType"]

        assert sfms_daily_actuals_mapper([raw]) == []

    def test_filters_station_with_null_coordinates(self):
        raw = _make_raw_daily(100, lat=None, lon=None, temperature=20.0)

        assert sfms_daily_actuals_mapper([raw], [station]) == []


class TestSfmsDailyForecastsMapper:
    def test_maps_forecast_and_computes_dewpoint(self):
        raw = _make_raw_daily(
            100,
            record_type="FORECAST",
            temperature=20.0,
            relativeHumidity=50.0,
            precipitation=2.5,
            windSpeed=10.0,
            windDirection=180.0,
            fineFuelMoistureCode=85.0,
            duffMoistureCode=30.0,
            droughtCode=200.0,
        )

        result = sfms_daily_forecasts_mapper([raw])

        assert len(result) == 1
        forecast = result[0]
        assert forecast.code == 100
        assert forecast.lat == approx(49.0, abs=0)
        assert forecast.lon == approx(-123.0, abs=0)
        assert forecast.elevation == 150
        assert forecast.temperature == approx(20.0)
        assert forecast.relative_humidity == approx(50.0)
        assert forecast.dewpoint == approx(9.28, abs=0.01)
        assert forecast.precipitation == approx(2.5)
        assert forecast.wind_speed == approx(10.0)
        assert forecast.wind_direction == approx(180.0)
        assert forecast.ffmc is None
        assert forecast.dmc is None
        assert forecast.dc is None

    def test_filters_actual_record_type(self):
        raw = _make_raw_daily(100, record_type="ACTUAL", temperature=20.0)

        assert sfms_daily_forecasts_mapper([raw]) == []

    def test_filters_manual_record_type(self):
        raw = _make_raw_daily(100, record_type="MANUAL", temperature=20.0)

        assert sfms_daily_forecasts_mapper([raw]) == []

    def test_empty_raw_dailies(self):
        assert sfms_daily_actuals_mapper([]) == []

    def test_multiple_stations_mixed_records(self):
        raw_dailies = [
            _make_raw_daily(100, temperature=10.0),
            _make_raw_daily(200, record_type="FORECAST", temperature=20.0),
            _make_raw_daily(200, lat=50.0, lon=-124.0, elevation=300, temperature=25.0),
            _make_raw_daily(100, status="INACTIVE", temperature=30.0),
        ]

        result = sfms_daily_actuals_mapper(raw_dailies)

        assert len(result) == 2
        assert result[0].code == 100
        assert result[0].temperature == pytest.approx(10.0)
        assert result[1].code == 200
        assert result[1].temperature == pytest.approx(25.0)

    def test_uses_daily_station_metadata(self):
        raw = _make_raw_daily(100, lat=49.0, lon=-123.0, elevation=150, temperature=5.0)

        result = sfms_daily_actuals_mapper([raw])

        assert result[0].lat == pytest.approx(49.0)
        assert result[0].lon == pytest.approx(-123.0)
        assert result[0].elevation == 150
