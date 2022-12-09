""" Unit testing for hourly actuals job """
from zoneinfo import ZoneInfo
from datetime import date
from tileserv.tools.time import morning_time, noon_time, evening_time

input_datetime = date.fromisoformat("2022-12-01")
timezone_info = ZoneInfo("America/Vancouver")


def test_pin_to_morning_time():
    """ Pinning a date to morning should be 8am PDT """
    morning_datetime = morning_time(input_datetime)

    assert morning_datetime.year == 2022
    assert morning_datetime.month == 12
    assert morning_datetime.day == 1
    assert morning_datetime.hour == 8
    assert morning_datetime.minute == 0
    assert morning_datetime.second == 0
    assert morning_datetime.timetz().tzinfo == timezone_info


def test_pin_to_noon_time():
    """ Pinning a date to morning should be 8am PDT """
    noon_datetime = noon_time(input_datetime)

    assert noon_datetime.year == 2022
    assert noon_datetime.month == 12
    assert noon_datetime.day == 1
    assert noon_datetime.hour == 13
    assert noon_datetime.minute == 0
    assert noon_datetime.second == 0
    assert noon_datetime.timetz().tzinfo == timezone_info


def test_pin_to_evening_time():
    """ Pinning a date to morning should be 8am PDT """
    evening_datetime = evening_time(input_datetime)

    assert evening_datetime.year == 2022
    assert evening_datetime.month == 12
    assert evening_datetime.day == 1
    assert evening_datetime.hour == 16
    assert evening_datetime.minute == 45
    assert evening_datetime.second == 0
    assert evening_datetime.timetz().tzinfo == timezone_info
