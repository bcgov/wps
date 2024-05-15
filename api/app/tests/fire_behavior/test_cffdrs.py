from datetime import datetime
import pandas as pd
import numpy as np
import rpy2.robjects as robjs
import pytest
import math
from app.schemas.fba_calc import FuelTypeEnum
from app.fire_behaviour import cffdrs
from app.fire_behaviour.cffdrs import (pandas_to_r_converter, hourly_fine_fuel_moisture_code, CFFDRSException)


start_date = datetime(2023, 8, 17)
end_date = datetime(2023, 8, 18)
hourly_datetimes = pd.date_range(start=start_date, end=end_date, freq='H')

hourly_data = {
    'datetime': hourly_datetimes,
    'temp': np.random.default_rng(111).uniform(20.0, 30.0, size=len(hourly_datetimes)),
    'rh': np.random.default_rng(111).uniform(40.0, 100.0, size=len(hourly_datetimes)),
    'precipitation': np.random.default_rng(111).uniform(0.0, 1.0, size=len(hourly_datetimes)),
    'ws': np.random.default_rng(111).uniform(0.0, 30.0, size=len(hourly_datetimes)),
}

df_hourly = pd.DataFrame(hourly_data)


def test_pandas_to_r_converter():
    r_df = pandas_to_r_converter(df_hourly)

    assert isinstance(r_df, robjs.vectors.DataFrame)


def test_hourly_ffmc_calculates_values():
    ffmc_old = 80.0
    df = hourly_fine_fuel_moisture_code(df_hourly, ffmc_old)
    
    assert not df['hffmc'].isnull().any()


def test_hourly_ffmc_no_temperature():
    ffmc_old = 80.0
    df_hourly = pd.DataFrame({'datetime': [hourly_datetimes[0], hourly_datetimes[1]], 'celsius': [12, 1], 'precipitation': [0, 1], 'ws': [14, 12], 'rh':[50, 50]})

    with pytest.raises(CFFDRSException):
        hourly_fine_fuel_moisture_code(df_hourly, ffmc_old)
    

def test_ros():
    """ ROS runs """
    ros =cffdrs.rate_of_spread(FuelTypeEnum.C7, 1, 1, 1, 1, pc=100, pdf=None,
                                 cc=None, cbh=10)
    assert math.isclose(ros, 1.2966988409822604e-05)


def test_ros_no_isi():
    """ ROS fails """
    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.rate_of_spread(FuelTypeEnum.C7, None, 1, 1, 1, pc=100, pdf=None,
                              cc=None, cbh=10)


def test_ros_no_bui():
    """ ROS fails """
    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.rate_of_spread(FuelTypeEnum.C7, 1, None, 1, 1, pc=100, pdf=None,
                              cc=None, cbh=10)


def test_ros_no_params():
    """ ROS fails """
    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.rate_of_spread(FuelTypeEnum.C7, None, None, None, None, pc=100, pdf=None,
                              cc=None, cbh=10)

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
    """ Test that we can handle None values when attempting to calculate ffmc """
    res = cffdrs.fine_fuel_moisture_code(ffmc=ffmc, 
                                        temperature=temperature,
                                        precipitation=precipitation,
                                        relative_humidity=relative_humidity,
                                        wind_speed=wind_speed)
    assert res is None