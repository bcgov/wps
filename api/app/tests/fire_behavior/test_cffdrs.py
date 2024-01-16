from datetime import datetime
import pandas as pd
import numpy as np
import rpy2.robjects as robjs
import pytest
import math
from app.schemas.fba_calc import FuelTypeEnum
from app.fire_behaviour import cffdrs
from app.fire_behaviour.cffdrs import (pandas_to_r_converter, hourly_fine_fuel_moisture_code)


start_date = datetime(2023, 8, 17)
end_date = datetime(2023, 8, 18)
hourly_datetimes = pd.date_range(start=start_date, end=end_date, freq='H')

hourly_data = {
    'datetime': hourly_datetimes,
    'temp': np.random.default_rng(111).uniform(20.0, 30.0, size=len(hourly_datetimes)),
    'rh': np.random.default_rng(111).uniform(40.0, 100.0, size=len(hourly_datetimes)),
    'precip': np.random.default_rng(111).uniform(0.0, 1.0, size=len(hourly_datetimes)),
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

