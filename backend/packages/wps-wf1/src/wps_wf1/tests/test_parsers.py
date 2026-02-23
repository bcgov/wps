from datetime import datetime, timezone
import math
import pytest
from wps_wf1.parsers import parse_hourly_actual, sfms_daily_actuals_mapper

from wps_shared.db.models.observations import HourlyActual
from wps_shared.schemas.sfms import SFMSDailyActual
from wps_shared.schemas.stations import WFWXWeatherStation


def _make_station(code, lat=49.0, lon=-123.0, elevation=100):
    return WFWXWeatherStation(
        wfwx_id=f"wfwx-{code}",
        code=code,
        name=f"S{code}",
        latitude=lat,
        longitude=lon,
        elevation=elevation,
        zone_code=None,
    )


def _make_raw_daily(
    station_code, record_type="ACTUAL", status="ACTIVE", lat=49.0, lon=-123.0, **weather_fields
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
            "latitude": lat,
            "longitude": lon,
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
        station = _make_station(100, lat=49.0, lon=-123.0, elevation=150)
        raw = _make_raw_daily(
            100,
            temperature=15.0,
            relativeHumidity=50.0,
            precipitation=2.5,
            windSpeed=10.0,
            windDirection=180.0,
            fineFuelMoistureCode=85.0,
            duffMoistureCode=30.0,
            droughtCode=200.0,
        )

        result = sfms_daily_actuals_mapper([raw], [station])

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
        station = _make_station(100)
        raw = _make_raw_daily(100)

        result = sfms_daily_actuals_mapper([raw], [station])

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

    def test_filters_forecast_record_type(self):
        station = _make_station(100)
        raw = _make_raw_daily(100, record_type="FORECAST", temperature=20.0)

        assert sfms_daily_actuals_mapper([raw], [station]) == []

    def test_filters_inactive_station(self):
        station = _make_station(100)
        raw = _make_raw_daily(100, status="INACTIVE", temperature=20.0)

        assert sfms_daily_actuals_mapper([raw], [station]) == []

    def test_filters_station_with_null_coordinates(self):
        station = _make_station(100)
        raw = _make_raw_daily(100, lat=None, lon=None, temperature=20.0)

        assert sfms_daily_actuals_mapper([raw], [station]) == []

    def test_empty_raw_dailies(self):
        station = _make_station(100)

        assert sfms_daily_actuals_mapper([], [station]) == []

    def test_multiple_stations_mixed_records(self):
        stations = [
            _make_station(100, lat=49.0, lon=-123.0, elevation=100),
            _make_station(200, lat=50.0, lon=-124.0, elevation=300),
        ]
        raw_dailies = [
            _make_raw_daily(100, temperature=10.0),
            _make_raw_daily(200, record_type="FORECAST", temperature=20.0),
            _make_raw_daily(200, temperature=25.0),
            _make_raw_daily(100, status="INACTIVE", temperature=30.0),
        ]

        result = sfms_daily_actuals_mapper(raw_dailies, stations)

        assert len(result) == 2
        assert result[0].code == 100
        assert result[0].temperature == pytest.approx(10.0)
        assert result[1].code == 200
        assert result[1].temperature == pytest.approx(25.0)

    def test_uses_station_coordinates_not_daily(self):
        """Station lat/lon/elevation come from the station lookup, not the raw daily."""
        station = _make_station(100, lat=51.0, lon=-125.0, elevation=999)
        raw = _make_raw_daily(100, lat=49.0, lon=-123.0, temperature=5.0)

        result = sfms_daily_actuals_mapper([raw], [station])

        assert result[0].lat == pytest.approx(51.0)
        assert result[0].lon == pytest.approx(-125.0)
        assert result[0].elevation == 999
