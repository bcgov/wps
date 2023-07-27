""" Unit testing for WFWX API validation """
import math
from datetime import datetime
from app.schemas.observations import WeatherReading
from app.wildfire_one.validation import validate_metric, get_valid_flags


def test_validate_metric_below():
    """ Below range returns false """
    result = validate_metric(1, 2, 3)
    assert result is False


def test_validate_metric_above():
    """ Above range returns false """
    result = validate_metric(3, 1, 2)
    assert result is False


def test_validate_metric_within():
    """ Within range returns true """
    result = validate_metric(2, 1, 3)
    assert result is True


def test_validate_metric_at_low():
    """ At lower bound returns true """
    result = validate_metric(1, 1, 2)
    assert result is True


def test_validate_metric_at_high():
    """ At lower bound returns true """
    result = validate_metric(2, 1, 2)
    assert result is True


def test_temp_valid():
    """ Any temp number is valid"""
    test_record = WeatherReading(datetime=datetime(2023, 7, 26, 12, 30, 15),
                                 temperature=1,
                                 relative_humidity=None,
                                 wind_speed=None,
                                 wind_direction=None,
                                 precipitation=None)
    temp_valid, _, _, _, _ = get_valid_flags(test_record)
    assert temp_valid is True


def test_temp_invalid():
    """ No temp number is invalid"""
    test_record = WeatherReading(datetime=datetime(2023, 7, 26, 12, 30, 15),
                                 temperature=None,
                                 relative_humidity=None,
                                 wind_speed=None,
                                 wind_direction=None,
                                 precipitation=None)
    temp_valid, _, _, _, _ = get_valid_flags(test_record)
    assert temp_valid is False


def test_rh_valid():
    """ 0 to 100 is valid for rh"""
    low_valid = WeatherReading(datetime=datetime(2023, 7, 26, 12, 30, 15),
                               temperature=None,
                               relative_humidity=0,
                               wind_speed=None,
                               wind_direction=None,
                               precipitation=None)
    _, low_rh_valid, _, _, _ = get_valid_flags(low_valid)
    assert low_rh_valid is True

    high_valid = WeatherReading(datetime=datetime(2023, 7, 26, 12, 30, 15),
                                temperature=None,
                                relative_humidity=100,
                                wind_speed=None,
                                wind_direction=None,
                                precipitation=None)
    _, high_rh_valid, _, _, _ = get_valid_flags(high_valid)
    assert high_rh_valid is True


def test_rh_invalid():
    """ Below 0 and above 100 is invalid for rh"""
    low_valid = WeatherReading(datetime=datetime(2023, 7, 26, 12, 30, 15),
                               temperature=None,
                               relative_humidity=-1,
                               wind_speed=None,
                               wind_direction=None,
                               precipitation=None)
    _, low_rh_invalid, _, _, _ = get_valid_flags(low_valid)
    assert low_rh_invalid is False

    high_valid = WeatherReading(datetime=datetime(2023, 7, 26, 12, 30, 15),
                                temperature=None,
                                relative_humidity=101,
                                wind_speed=None,
                                wind_direction=None,
                                precipitation=None)
    _, high_rh_invalid, _, _, _ = get_valid_flags(high_valid)
    assert high_rh_invalid is False


def test_wind_speed_valid():
    """ 0 to inf is valid for wind_speed"""
    low_valid = WeatherReading(datetime=datetime(2023, 7, 26, 12, 30, 15),
                               temperature=None,
                               relative_humidity=None,
                               wind_speed=0,
                               wind_direction=None,
                               precipitation=None)
    _, _, low_wind_speed_valid, _, _ = get_valid_flags(low_valid)
    assert low_wind_speed_valid is True

    high_valid = WeatherReading(datetime=datetime(2023, 7, 26, 12, 30, 15),
                                temperature=None,
                                relative_humidity=None,
                                wind_speed=math.inf,
                                wind_direction=None,
                                precipitation=None)
    _, _, high_wind_speed_valid, _, _ = get_valid_flags(high_valid)
    assert high_wind_speed_valid is True


def test_wind_speed_invalid():
    """ Below 0 is invalid for wind_speed"""
    low_valid = WeatherReading(datetime=datetime(2023, 7, 26, 12, 30, 15),
                               temperature=None,
                               relative_humidity=None,
                               wind_speed=-1,
                               wind_direction=None,
                               precipitation=None)
    _, _, low_wind_speed_invalid, _, _ = get_valid_flags(low_valid)
    assert low_wind_speed_invalid is False


def test_wdir_valid():
    """ 0 to 360 is valid for wdir"""
    low_valid = WeatherReading(datetime=datetime(2023, 7, 26, 12, 30, 15),
                               temperature=None,
                               relative_humidity=None,
                               wind_speed=None,
                               wind_direction=0,
                               precipitation=None)
    _, _, _, low_wdir_valid, _ = get_valid_flags(low_valid)
    assert low_wdir_valid is True

    high_valid = WeatherReading(datetime=datetime(2023, 7, 26, 12, 30, 15),
                                temperature=None,
                                relative_humidity=None,
                                wind_speed=None,
                                wind_direction=360,
                                precipitation=None)
    _, _, _, high_wdir_valid, _ = get_valid_flags(high_valid)
    assert high_wdir_valid is True


def test_wdir_invalid():
    """ Below 0 and above 360 is invalid for wdir"""
    low_valid = WeatherReading(datetime=datetime(2023, 7, 26, 12, 30, 15),
                               temperature=None,
                               relative_humidity=None,
                               wind_speed=None,
                               wind_direction=-1,
                               precipitation=None)
    _, _, _, low_wdir_invalid, _ = get_valid_flags(low_valid)
    assert low_wdir_invalid is False

    high_valid = WeatherReading(datetime=datetime(2023, 7, 26, 12, 30, 15),
                                temperature=None,
                                relative_humidity=None,
                                wind_speed=None,
                                wind_direction=361,
                                precipitation=None)
    _, _, _, high_wdir_invalid, _ = get_valid_flags(high_valid)
    assert high_wdir_invalid is False


def test_precip_valid():
    """ 0 to inf is valid for precip"""
    low_valid = WeatherReading(datetime=datetime(2023, 7, 26, 12, 30, 15),
                               temperature=None,
                               relative_humidity=None,
                               wind_speed=None,
                               wind_direction=None,
                               precipitation=0)
    _, _, _, _, low_precip_valid = get_valid_flags(low_valid)
    assert low_precip_valid is True

    high_valid = WeatherReading(datetime=datetime(2023, 7, 26, 12, 30, 15),
                                temperature=None,
                                relative_humidity=None,
                                wind_speed=None,
                                wind_direction=None,
                                precipitation=math.inf)
    _, _, _, _, high_precip_valid = get_valid_flags(high_valid)
    assert high_precip_valid is True


def test_precip_invalid():
    """ Below 0 is invalid for precip"""
    low_valid = WeatherReading(datetime=datetime(2023, 7, 26, 12, 30, 15),
                               temperature=None,
                               relative_humidity=None,
                               wind_speed=None,
                               wind_direction=None,
                               precipitation=-1)
    _, _, _, _, low_precip_invalid = get_valid_flags(low_valid)
    assert low_precip_invalid is False
