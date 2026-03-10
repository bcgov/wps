import math
from datetime import datetime

import numpy as np
import pandas as pd
import pytest
from app.fire_behaviour import cffdrs
from app.fire_behaviour.prediction import calculate_cfb
from wps_shared.fuel_types import FuelTypeEnum

start_date = datetime(2023, 8, 17)
end_date = datetime(2023, 8, 18)
hourly_datetimes = pd.date_range(start=start_date, end=end_date, freq="H")

hourly_data = {
    "temperature": np.random.default_rng(111).uniform(20.0, 30.0, size=len(hourly_datetimes)),
    "relative_humidity": np.random.default_rng(111).uniform(
        40.0, 100.0, size=len(hourly_datetimes)
    ),
    "precipitation": np.random.default_rng(111).uniform(0.0, 1.0, size=len(hourly_datetimes)),
    "wind_speed": np.random.default_rng(111).uniform(0.0, 30.0, size=len(hourly_datetimes)),
}

df_hourly = pd.DataFrame(hourly_data)


def test_ros():
    """ROS runs"""
    ros = cffdrs.rate_of_spread(FuelTypeEnum.C7, 1, 1, 1, 1, pc=100, pdf=None, cc=None, cbh=10)
    assert math.isclose(ros, 1.2966988409822604e-05)


def test_ros_no_isi():
    """ROS fails"""
    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.rate_of_spread(FuelTypeEnum.C7, None, 1, 1, 1, pc=100, pdf=None, cc=None, cbh=10)


def test_ros_no_bui():
    """ROS fails"""
    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.rate_of_spread(FuelTypeEnum.C7, 1, None, 1, 1, pc=100, pdf=None, cc=None, cbh=10)


def test_ros_no_params():
    """ROS fails"""
    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.rate_of_spread(
            FuelTypeEnum.C7, None, None, None, None, pc=100, pdf=None, cc=None, cbh=10
        )


@pytest.mark.parametrize(
    "ffmc,temperature,precipitation,relative_humidity,wind_speed",
    [
        (None, 10, 9, 8, 7),
        (11, None, 9, 8, 7),
        (11, 10, None, 8, 7),
        (11, 10, 9, None, 7),
        (11, 10, 9, 8, None),
        (None, None, None, 8, 7),
        (None, None, None, None, None),
    ],
)
def test_failing_ffmc(ffmc, temperature, precipitation, relative_humidity, wind_speed):
    """Test that we can handle None values when attempting to calculate ffmc"""
    res = cffdrs.fine_fuel_moisture_code(
        ffmc=ffmc,
        temperature=temperature,
        precipitation=precipitation,
        relative_humidity=relative_humidity,
        wind_speed=wind_speed,
    )
    assert res is None


@pytest.mark.parametrize(
    "dmc,temperature,relative_humidity,precipitation",
    [(None, 10, 90, 1), (100, None, 90, 1), (100, 10, None, 1), (100, 10, 90, None)],
)
def test_failing_dmc(dmc, temperature, relative_humidity, precipitation):
    """Test that we can handle None values when attempting to calculate dmc"""
    res = cffdrs.duff_moisture_code(dmc, temperature, relative_humidity, precipitation)
    assert res is None


@pytest.mark.parametrize(
    "dc,temperature,relative_humidity,precipitation",
    [(None, 10, 90, 1), (100, None, 90, 1), (100, 10, 90, None)],
)
def test_failing_dc(dc, temperature, relative_humidity, precipitation):
    """Test that we can handle None values when attempting to calculate dc"""
    res = cffdrs.drought_code(dc, temperature, relative_humidity, precipitation)
    assert res is None


@pytest.mark.parametrize(
    "ffmc,wind_speed",
    [(None, 10), (11, None), (None, None)],
)
def test_failing_isi(ffmc, wind_speed):
    """ISI returns None when any input is None."""
    assert cffdrs.initial_spread_index(ffmc, wind_speed) is None


@pytest.mark.parametrize(
    "isi,bui",
    [(None, 50), (20, None), (None, None)],
)
def test_failing_fwi(isi, bui):
    """FWI returns None when any input is None."""
    assert cffdrs.fire_weather_index(isi, bui) is None


@pytest.mark.parametrize(
    "dmc,dc",
    [(None, 100), (50, None), (None, None)],
)
def test_failing_bui(dmc, dc):
    """BUI returns None when any input is None."""
    assert cffdrs.bui_calc(dmc, dc) is None


def test_none_latitude_dmc():
    res = cffdrs.duff_moisture_code(100, 10, 90, 0, latitude=None)
    assert res is not None


def test_none_month_dmc():
    res = cffdrs.duff_moisture_code(100, 10, 90, 0, month=None)
    assert res is not None


def test_none_latitude_dc():
    res = cffdrs.drought_code(100, 10, 90, 0, latitude=None)
    assert res is not None


def test_none_month_dc():
    res = cffdrs.drought_code(100, 10, 90, 0, month=None)
    assert res is not None


def test_dmc_temp_below_threshold_gives_zero_drying():
    """cffdrs_py clamps temp to -1.1 when temp < 1.1°C (Eq. 16), making drying rate rk = 0.
    With no precipitation and a low initial DMC, the result stays at the initial value."""
    # temp=1.0 is below the 1.1°C threshold — rk = 1.894 * (-1.1 + 1.1) * ... = 0
    res_below = cffdrs.duff_moisture_code(10, 1.0, 50, 0)
    # temp=1.2 is above the threshold — rk > 0, so DMC increases slightly
    res_above = cffdrs.duff_moisture_code(10, 1.2, 50, 0)
    assert res_below < res_above


def test_dmc_temp_at_threshold_gives_zero_drying():
    """At exactly 1.1°C, temp is not clamped (condition is temp < 1.1), so rk is a small positive value."""
    res_at = cffdrs.duff_moisture_code(10, 1.1, 50, 0)
    res_below = cffdrs.duff_moisture_code(10, 1.0, 50, 0)
    assert res_at >= res_below


def test_back_rate_of_spread_requires_wsv():
    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.back_rate_of_spread(FuelTypeEnum.C7, ffmc=85.0, bui=50.0, wsv=None, fmc=100.0, sfc=1.5, pc=None, cc=None, pdf=None, cbh=7.0)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"bui": 80.0},  # missing isi
        {"isi": 20.0},  # missing bui
        {},             # missing both
    ],
)
def test_crown_fraction_burned_c6_requires_isi_and_bui(kwargs):
    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.crown_fraction_burned(FuelTypeEnum.C6, fmc=100.0, sfc=0.5, ros=15.0, cbh=7.0, **kwargs)


def test_crown_fraction_burned_c6_returns_valid_cfb():
    """C6 CFB is between 0 and 1 with crown-burning conditions."""
    cfb = cffdrs.crown_fraction_burned(FuelTypeEnum.C6, fmc=100.0, sfc=0.5, ros=15.0, cbh=7.0, isi=20.0, bui=80.0)
    assert 0.0 <= cfb <= 1.0



def test_crown_fraction_burned_non_c6_does_not_require_isi_bui():
    """Non-C6 fuel types work without isi/bui."""
    cfb = cffdrs.crown_fraction_burned(FuelTypeEnum.C7, fmc=100.0, sfc=0.5, ros=15.0, cbh=7.0)
    assert 0.0 <= cfb <= 1.0


def test_calculate_cfb_c6_threads_isi_bui():
    """calculate_cfb passes isi and bui through to crown_fraction_burned for C6."""
    cfb = calculate_cfb(FuelTypeEnum.C6, fmc=100.0, sfc=0.5, ros=15.0, cbh=7.0, isi=20.0, bui=80.0)
    assert cfb is not None
    assert 0.0 <= cfb <= 1.0


def test_calculate_cfb_c6_missing_isi_bui_raises():
    """calculate_cfb raises for C6 when isi/bui not provided."""
    with pytest.raises(cffdrs.CFFDRSException):
        calculate_cfb(FuelTypeEnum.C6, fmc=100.0, sfc=0.5, ros=15.0, cbh=7.0)


@pytest.mark.parametrize(
    "fuel_type",
    [FuelTypeEnum.D1, FuelTypeEnum.O1A, FuelTypeEnum.O1B, FuelTypeEnum.S1, FuelTypeEnum.S2, FuelTypeEnum.S3],
)
def test_calculate_cfb_returns_zero_for_no_crown_fuel_types(fuel_type):
    """Fuel types without crowns return 0 regardless of inputs."""
    assert calculate_cfb(fuel_type, fmc=100.0, sfc=0.5, ros=15.0, cbh=7.0) == 0
