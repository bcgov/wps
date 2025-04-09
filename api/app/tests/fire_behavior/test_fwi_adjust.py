import math
from wps_shared.fuel_types import FuelTypeEnum
from app.fire_behaviour.fwi_adjust import calculate_adjusted_fwi_result
from wps_shared.schemas.fba_calc import StationRequest


def test_adjusted_fwi_result_no_wind_speed_no_precipitation():
    adjusted_fwi_result = calculate_adjusted_fwi_result(
        requested_station=StationRequest(station_code=1, fuel_type=FuelTypeEnum.C2),
        yesterday={"fineFuelMoistureCode": 1},
        raw_daily={
            "buildUpIndex": 1,
            "duffMoistureCode": 1,
            "droughtCode": 1,
            "temperature": 1,
            "relativeHumidity": 1,
            "precipitation": 1,
            "windSpeed": 1,
            "recordType": {"id": "ACTUAL"},
        },
    )
    assert math.isclose(adjusted_fwi_result.bui, 0.606, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.ffmc, 26.757, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.isi, 0.001, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.precipitation, 1.0, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.wind_speed, 1.0, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.fwi, 0.0, abs_tol=0.001)
    assert adjusted_fwi_result.status == "ACTUAL"


def test_adjusted_fwi_result_with_wind_speed():
    adjusted_fwi_result = calculate_adjusted_fwi_result(
        requested_station=StationRequest(station_code=1, fuel_type=FuelTypeEnum.C2, wind_speed=5),
        yesterday={"fineFuelMoistureCode": 1},
        raw_daily={
            "buildUpIndex": 1,
            "duffMoistureCode": 1,
            "droughtCode": 1,
            "temperature": 1,
            "relativeHumidity": 1,
            "precipitation": 1,
            "windSpeed": 1,
            "recordType": {"id": "ACTUAL"},
        },
    )
    assert math.isclose(adjusted_fwi_result.bui, 0.606, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.ffmc, 31.427, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.isi, 0.006, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.wind_speed, 5.0, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.fwi, 0.001, abs_tol=0.001)
    assert adjusted_fwi_result.status == "ADJUSTED"


def test_adjusted_fwi_result_with_precipitation():
    adjusted_fwi_result = calculate_adjusted_fwi_result(
        requested_station=StationRequest(station_code=1, fuel_type=FuelTypeEnum.C2, precipitation=25),
        yesterday={"fineFuelMoistureCode": 1},
        raw_daily={
            "buildUpIndex": 1,
            "duffMoistureCode": 1,
            "droughtCode": 1,
            "temperature": 1,
            "relativeHumidity": 1,
            "precipitation": 1,
            "windSpeed": 1,
            "recordType": {"id": "ACTUAL"},
        },
    )
    assert math.isclose(adjusted_fwi_result.bui, 0.606, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.ffmc, 26.757, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.isi, 0.001, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.precipitation, 25.0, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.wind_speed, 1.0, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.fwi, 0.0, abs_tol=0.001)
    assert adjusted_fwi_result.status == "ADJUSTED"