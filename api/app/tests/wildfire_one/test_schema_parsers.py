from typing import List
from wps_shared.schemas.morecast_v2 import StationDailyFromWF1, WeatherDeterminate
from wps_shared.wildfire_one.schema_parsers import (
    WF1RecordTypeEnum,
    parse_noon_forecast,
    parse_hourly_actual,
    unique_weather_stations_mapper,
    weather_indeterminate_list_mapper,
    weather_stations_mapper,
    dailies_list_mapper,
)
import pytest


def build_mock_station_group_member(station_id: str, station_code: str):
    return {
        "station": {
            "id": station_id,
            "stationCode": station_code,
            "stationStatus": {
                "id": '1'
            },
            "displayLabel": 's1',
            "fireCentre": {
                "id": '1',
                "displayLabel": "fc1"
            },
            "zone": {
                "id": "1",
                "displayLabel": 'z1',
                'fireCentre': 'fc1'
            }
        }
    }


def test_forecast_valid_flags_are_set():
    """ Noon forecast valid flags are set """
    raw_forecast = {
        "weatherTimestamp": 1,
        'updateDate': 1,
        "station_code": 1,
        "temperature": 1,
        "relativeHumidity": 1,
        "windSpeed": 1,
        "windDirection": 1,
        "precipitation": 1,
        "grasslandCuring": 1,
        "fineFuelMoistureCode": 1,
        "duffMoistureCode": 1,
        "droughtCode": 1,
        "initialSpreadIndex": 1,
        "buildUpIndex": 1,
        "fireWeatherIndex": 1,
        "dailySeverityRating": 1
    }

    result = parse_noon_forecast(1, raw_forecast)
    assert result.temp_valid is True
    assert result.rh_valid is True
    assert result.wspeed_valid is True
    assert result.wdir_valid is True
    assert result.precip_valid is True


def test_actual_valid_flags_are_set():
    """ Noon forecast valid flags are set """
    raw_hourly_actual = {
        "weatherTimestamp": 1,
        'updateDate': 1,
        "station_code": 1,
        "temperature": 1,
        "relativeHumidity": 1,
        "windSpeed": 1,
        "windDirection": 1,
        "precipitation": 1,
        "grasslandCuring": 1,
        "fineFuelMoistureCode": 1,
        "duffMoistureCode": 1,
        "droughtCode": 1,
        "initialSpreadIndex": 1,
        "buildUpIndex": 1,
        "fireWeatherIndex": 1,
        "dailySeverityRating": 1,
        "observationValidInd": True,
        "observationValidComment": ''
    }

    result = parse_hourly_actual(1, raw_hourly_actual)
    assert result.temp_valid is True
    assert result.rh_valid is True
    assert result.wspeed_valid is True
    assert result.wdir_valid is True
    assert result.precip_valid is True


def test_unique_station_mapper_duplicate():
    """ Returns unique stations from raw list of stations """
    stations = [
        build_mock_station_group_member("1", "1"),
        build_mock_station_group_member("1", "1")
    ]

    result = unique_weather_stations_mapper(stations)
    assert len(result) == 1
    assert result[0].station_code == 1


def test_unique_station_mapper_unique():
    """ Returns unique stations from non duplicate station list """
    stations = [
        build_mock_station_group_member("1", "1"),
        build_mock_station_group_member("2", "2")
    ]
    result = unique_weather_stations_mapper(stations)
    assert len(result) == 2
    assert result[0].station_code != result[1].station_code


def test_station_mapper():
    """ Returns stations based on raw wf1 stations """
    stations = [
        build_mock_station_group_member("1", "1"),
        build_mock_station_group_member("2", "2")
    ]
    result = weather_stations_mapper(stations)
    assert len(result) == 2
    assert result[0].station_code == 1
    assert result[0].id == '1'
    assert result[1].station_code == 2
    assert result[1].id == '2'


async def async_observed_dailies(record_type: str):
    yield {
        "createdBy": "test_user",
        "id": "test_guid_id",
        "stationData": {
            "stationCode": 1,
            "displayLabel": "Test",
            "latitude": 1,
            "longitude": 1,
            "stationStatus": {
                "id": "ACTIVE",
            },
        },
        "recordType": {
            "id": record_type
        },
        "weatherTimestamp": 1680984000000,
        "temperature": 1,
        "relativeHumidity": 1,
        "precipitation": 1,
        "windDirection": 1,
        "windSpeed": 1,
        "fineFuelMoistureCode": 1,
        "duffMoistureCode": 1,
        "droughtCode": 1,
        "initialSpreadIndex": 1,
        "buildUpIndex": 1,
        "fireWeatherIndex": 1,
        "dangerForest": 1
    }


@pytest.mark.anyio
async def test_dailies_list_mapper_actual_daily_and_actual_filter(anyio_backend):
    result: List[StationDailyFromWF1] = await dailies_list_mapper(async_observed_dailies("ACTUAL"), WF1RecordTypeEnum.ACTUAL)
    assert len(result) == 1
    assert result[0].station_code == 1


@pytest.mark.anyio
async def test_dailies_list_mapper_actual_daily_and_forecast_filter(anyio_backend):
    result: List[StationDailyFromWF1] = await dailies_list_mapper(async_observed_dailies("ACTUAL"), WF1RecordTypeEnum.FORECAST)
    assert len(result) == 0


@pytest.mark.anyio
async def test_dailies_list_mapper_forecast_daily_and_forecast_filter(anyio_backend):
    result: List[StationDailyFromWF1] = await dailies_list_mapper(async_observed_dailies("FORECAST"), WF1RecordTypeEnum.FORECAST)
    assert len(result) == 1
    assert result[0].station_code == 1


@pytest.mark.anyio
async def test_dailies_list_mapper_forecast_daily_and_actual_filter(anyio_backend):
    result: List[StationDailyFromWF1] = await dailies_list_mapper(async_observed_dailies("FORECAST"), WF1RecordTypeEnum.ACTUAL)
    assert len(result) == 0


@pytest.mark.anyio
async def test_indeterminate_mapper_actual(anyio_backend):
    observed, forecast = await weather_indeterminate_list_mapper(async_observed_dailies("ACTUAL"))
    assert len(forecast) == 0
    assert len(observed) == 1
    assert observed[0].determinate == WeatherDeterminate.ACTUAL
    assert observed[0].station_code == 1


@pytest.mark.anyio
async def test_indeterminate_mapper_manual(anyio_backend):
    observed, forecast = await weather_indeterminate_list_mapper(async_observed_dailies("MANUAL"))
    assert len(forecast) == 0
    assert len(observed) == 1
    assert observed[0].determinate == WeatherDeterminate.ACTUAL
    assert observed[0].station_code == 1


@pytest.mark.anyio
async def test_indeterminate_mapper_forecast(anyio_backend):
    observed, forecast = await weather_indeterminate_list_mapper(async_observed_dailies("FORECAST"))
    assert len(observed) == 0
    assert len(forecast) == 1
    assert forecast[0].determinate == WeatherDeterminate.FORECAST
    assert forecast[0].station_code == 1
