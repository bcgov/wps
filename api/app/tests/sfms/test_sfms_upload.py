from unittest.mock import patch
from datetime import datetime, timezone
from app.routers.sfms import is_actual, get_target_filename


def get_pdt_8am():
    """ Morning SFMS runs some time in the morning
    Just to make everything extra confusing, use a PDT (-7) timestamp.
    """
    return datetime.fromisoformat('2022-08-23T08:17:50.947039-07:00')


def get_pdt_noon():
    """ NOT solar noon. Solar noon is at 12h00 PST / 13h00 PDT.
    Just to make everything extra confusing, use a PDT (-7) timestamp.
    """
    return datetime.fromisoformat('2022-08-23T12:17:50.947039-07:00')


def get_pdt_17():
    """ 17h00 PDT is 12h00 UTC the NEXT day.
    """
    return datetime.fromisoformat('2022-08-23T17:17:50.947039-07:00')


def get_pdt_1pm():
    """ Solar noon is at 12h00 PST / 13h00 PDT.
    Just to make everything extra confusing, use a PDT (-7) timestamp.
    """
    return datetime.fromisoformat('2022-08-23T13:17:50.947039-07:00')


def get_time_in_utc(date: datetime):
    """ Given some datetime, return the datetime in UTC """
    return date.astimezone(timezone.utc)


@patch('app.routers.sfms.get_pdt_now', return_value=get_pdt_8am())
def test_is_actual_before_noon(_):
    """ Test is_actual function """
    # If it's for yesterday, we assume it's an actual.
    assert is_actual('hfi20220822.tif') is True
    # If it's for today, we assume it's a forecast (actual only comes after SOLAR noon).
    assert is_actual('hfi20220823.tif') is False
    # If it's for tomorrow, we assume it's a forecast.
    assert is_actual('hfi20220824.tif') is False


@patch('app.routers.sfms.get_pdt_now', return_value=get_pdt_noon())
def test_is_actual_after_noon(_):
    """ Test is_actual function """
    # If it's for yesterday, we assume it's an actual.
    assert is_actual('hfi20220822.tif') is True
    # If it's for today, we assume it's an forecast, since it's BEFORE solar noon.
    assert is_actual('hfi20220823.tif') is False
    # If it's for tomorrow, we assume it's a forecast.
    assert is_actual('hfi20220824.tif') is False


@patch('app.routers.sfms.get_pdt_now', return_value=get_pdt_1pm())
def test_is_actual_after_solar_noon(_):
    """ Test is_actual function """
    # If it's for yesterday, we assume it's an actual.
    assert is_actual('hfi20220822.tif') is True
    # If it's for today, we assume it's an actual, since it's after SOLAR noon.
    assert is_actual('hfi20220823.tif') is True
    # If it's for tomorrow, we assume it's a forecast.
    assert is_actual('hfi20220824.tif') is False


@patch('app.routers.sfms.get_pdt_now', return_value=get_pdt_1pm())
def test_get_target_filename(_):
    """ Test get_target_filename function """
    # If it's for yesterday, we assume it's an actual.
    assert get_target_filename('hfi20220822.tif') == 'sfms/uploads/actual/2022-08-23/hfi20220822.tif'
    # If it's for today, after solar noon, we assume it's an actual.
    assert get_target_filename('hfi20220823.tif') == 'sfms/uploads/actual/2022-08-23/hfi20220823.tif'
    # If it's for tomorrow, we assume it's a forecast.
    assert get_target_filename('hfi20220824.tif') == 'sfms/uploads/forecast/2022-08-23/hfi20220824.tif'


@patch('app.routers.sfms.get_pdt_now', return_value=get_pdt_17())
def test_get_target_filename_day_difference(_):
    """ Test get_target_filename function, when UTC day is different from PST day """
    # If the issue date is today in Canada, we want the filename to reflect that.
    # We want to make sure that the fact that 5pm local on the 23rd, doesn't get construed as
    # the 24th. Yes. It's already the 24th in UTC - but we're only concerned with respect to
    # PDT.
    # Now sure. We could store the entire timestamp in the filename, and then we know exactly
    # what we're dealing with - but that seems excessive.
    assert get_target_filename('hfi20220822.tif') == 'sfms/uploads/actual/2022-08-23/hfi20220822.tif'
    # It's 5 pm, so anything for today, is an actual.
    assert get_target_filename('hfi20220823.tif') == 'sfms/uploads/actual/2022-08-23/hfi20220823.tif'
    # It's 5 pm, so anything for tomorrow, is a forecast.
    assert get_target_filename('hfi20220824.tif') == 'sfms/uploads/forecast/2022-08-23/hfi20220824.tif'
