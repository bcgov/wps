
from app.fire_behaviour.fuel_types import FuelTypeEnum
from app.fire_behaviour.wind_speed import calculate_wind_speed_result
from app.schemas.fba_calc import StationRequest, WindResult


def test_wind_speed_result_no_wind_speed():
    wind_speed_result = calculate_wind_speed_result(
        requested_station=StationRequest(station_code=1, fuel_type=FuelTypeEnum.C2),
        yesterday={'fineFuelMoistureCode': 1},
        raw_daily={'buildUpIndex': 1,
                   'temperature': 1,
                   'relativeHumidity': 1,
                   'precipitation': 1,
                   'windSpeed': 1,
                   'recordType': {'id': 'ACTUAL'}}
    )
    assert wind_speed_result == WindResult(
        ffmc=26.764851194872616,
        isi=0.0014066138707422092,
        wind_speed=1.0,
        fwi=0.00036937680245690413,
        status='ACTUAL')
