import math
from datetime import datetime

import pytest

from app.fire_behaviour.fwi_adjust import calculate_adjusted_fwi_result
from wps_shared.fuel_types import FuelTypeEnum
from wps_shared.schemas.fba_calc import StationRequest
from wps_shared.schemas.stations import WFWXWeatherStation

station_1 = WFWXWeatherStation(
    code=1,
    name="Noel",
    wfwx_id="one",
    latitude=55.2956,
    longitude=-120.4850,
    elevation=977,
    zone_code="T1",
)

time_of_interest = datetime.fromisoformat("2021-01-01")

yesterday = {"fineFuelMoistureCode": 1}
raw_daily = {
    "buildUpIndex": 1,
    "duffMoistureCode": 1,
    "droughtCode": 1,
    "temperature": 1,
    "relativeHumidity": 1,
    "precipitation": 1,
    "windSpeed": 1,
    "recordType": {"id": "ACTUAL"},
}


def test_adjusted_fwi_result_no_wind_speed_no_precipitation():
    adjusted_fwi_result = calculate_adjusted_fwi_result(
        requested_station=StationRequest(station_code=1, fuel_type=FuelTypeEnum.C2),
        wfwx_station=station_1,
        time_of_interest=time_of_interest,
        yesterday=yesterday,
        raw_daily=raw_daily,
    )
    assert math.isclose(adjusted_fwi_result.dmc, 1, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.dc, 1, abs_tol=0.001)
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
        wfwx_station=station_1,
        time_of_interest=time_of_interest,
        yesterday=yesterday,
        raw_daily=raw_daily,
    )
    assert math.isclose(adjusted_fwi_result.dmc, 1, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.dc, 1, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.bui, 0.606, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.ffmc, 31.427, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.isi, 0.006, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.wind_speed, 5.0, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.fwi, 0.001, abs_tol=0.001)
    assert adjusted_fwi_result.status == "ADJUSTED"


def test_adjusted_fwi_result_with_precipitation():
    adjusted_fwi_result = calculate_adjusted_fwi_result(
        requested_station=StationRequest(
            station_code=1, fuel_type=FuelTypeEnum.C2, precipitation=25
        ),
        wfwx_station=station_1,
        time_of_interest=time_of_interest,
        yesterday={
            **yesterday,
            "duffMoistureCode": 1,
            "droughtCode": 1,
        },
        raw_daily=raw_daily,
    )
    # dmc=0.0 because temperature=1 is below the 1.1°C threshold in cffdrs_py's DMC calculation
    # (Eq. 16): temp is clamped to -1.1, making the drying rate rk = 1.894*(−1.1+1.1)*... = 0.
    # The precipitation component (25mm, dmc_yda=1) also drives pr to 0 after clamping.
    # The previous R-based implementation did not apply this clamp and returned ~0.256.
    assert math.isclose(adjusted_fwi_result.dmc, 0.0, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.dc, 0.0, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.bui, 0.0, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.ffmc, 26.757, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.isi, 0.001, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.precipitation, 25.0, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.wind_speed, 1.0, abs_tol=0.001)
    assert math.isclose(adjusted_fwi_result.fwi, 0.0, abs_tol=0.001)
    assert adjusted_fwi_result.status == "ADJUSTED"


def test_adjusted_fwi_result_raises_when_weather_data_missing():
    raw_daily_missing = {
        "duffMoistureCode": None,
        "droughtCode": None,
        "temperature": None,
        "relativeHumidity": None,
        "precipitation": None,
        "windSpeed": None,
        "recordType": {"id": "ACTUAL"},
    }
    with pytest.raises(ValueError, match="Insufficient weather data"):
        calculate_adjusted_fwi_result(
            requested_station=StationRequest(station_code=1, fuel_type=FuelTypeEnum.C2),
            wfwx_station=station_1,
            time_of_interest=time_of_interest,
            yesterday={},
            raw_daily=raw_daily_missing,
        )
