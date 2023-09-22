import math
from app.fire_behaviour.fuel_types import FuelTypeEnum
from app.fire_behaviour.wind_speed import calculate_wind_speed_result
from app.schemas.fba_calc import StationRequest


def test_wind_speed_result_no_wind_speed():
    wind_speed_result = calculate_wind_speed_result(
        requested_station=StationRequest(station_code=1, fuel_type=FuelTypeEnum.C2),
        yesterday={'fineFuelMoistureCode': 1},
        raw_daily={'buildUpIndex': 1,
                   'duffMoistureCode': 1,
                   'droughtCode': 1,
                   'temperature': 1,
                   'relativeHumidity': 1,
                   'precipitation': 1,
                   'windSpeed': 1,
                   'recordType': {'id': 'ACTUAL'}}
    )
    assert math.isclose(wind_speed_result.bui, 0.606, abs_tol=0.001)
    assert math.isclose(wind_speed_result.ffmc, 26.765, abs_tol=0.001)
    assert math.isclose(wind_speed_result.isi, 0.001, abs_tol=0.001)
    assert math.isclose(wind_speed_result.wind_speed, 1.0, abs_tol=0.001)
    assert math.isclose(wind_speed_result.fwi, 0.0, abs_tol=0.001)
    assert wind_speed_result.status == 'ACTUAL'
