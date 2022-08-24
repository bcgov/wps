from unittest.mock import MagicMock, patch
from datetime import datetime
from app.routers.sfms import is_actual, get_target_filename


def mock_pst_8am():
    """ Morning SFMS runs some time in the morning
    Just to make everything extra confusing, use a PDT (-7) timestamp.
    """
    return datetime.fromisoformat('2022-08-23T08:17:50.947039-07:00')


def mock_pdt_noon():
    """ NOT solar noon. Solar noon is at 12h00 PST / 13h00 PDT.
    Just to make everything extra confusing, use a PDT (-7) timestamp.
    """
    return datetime.fromisoformat('2022-08-23T12:17:50.947039-07:00')


def mock_pdt_1pm():
    """ Solar noon is at 12h00 PST / 13h00 PDT.
    Just to make everything extra confusing, use a PDT (-7) timestamp.
    """
    return datetime.fromisoformat('2022-08-23T13:17:50.947039-07:00')


def mock_utc_20():
    """ Solar noon is at 20h00 UTC
    """
    return datetime.fromisoformat('2022-08-23T20:00:00.000000+00:00')


@patch('app.routers.sfms.get_pst_now', return_value=mock_pst_8am())
def test_is_actual_before_noon(_):
    """ Test is_actual function """
    # If it's for yesterday, we assume it's an actual.
    assert is_actual('hfi20220822.tif') is True
    # If it's for today, we assume it's a forecast (actual only comes after SOLAR noon).
    assert is_actual('hfi20220823.tif') is False
    # If it's for tomorrow, we assume it's a forecast.
    assert is_actual('hfi20220824.tif') is False


@patch('app.routers.sfms.get_pst_now', return_value=mock_pdt_noon())
def test_is_actual_after_noon(_):
    """ Test is_actual function """
    # If it's for yesterday, we assume it's an actual.
    assert is_actual('hfi20220822.tif') is True
    # If it's for today, we assume it's an forecast, since it's BEFORE solar noon.
    assert is_actual('hfi20220823.tif') is False
    # If it's for tomorrow, we assume it's a forecast.
    assert is_actual('hfi20220824.tif') is False


@patch('app.routers.sfms.get_pst_now', return_value=mock_pdt_1pm())
def test_is_actual_after_solar_noon(_):
    """ Test is_actual function """
    # If it's for yesterday, we assume it's an actual.
    assert is_actual('hfi20220822.tif') is True
    # If it's for today, we assume it's an actual, since it's after SOLAR noon.
    assert is_actual('hfi20220823.tif') is True
    # If it's for tomorrow, we assume it's a forecast.
    assert is_actual('hfi20220824.tif') is False


@patch('app.routers.sfms.get_pst_now', return_value=mock_pdt_1pm())
@patch('app.routers.sfms.get_utc_now', return_value=mock_utc_20())
def test_get_target_filename(_, __):
    """ Test get_target_filename function """
    # If it's for yesterday, we assume it's an actual.
    assert get_target_filename('hfi20220822.tif') == 'sfms/uploads/actual/2022-08-23/hfi20220822.tif'
    # If it's for today, after solar noon, we assume it's an actual.
    assert get_target_filename('hfi20220823.tif') == 'sfms/uploads/actual/2022-08-23/hfi20220823.tif'
    # If it's for tomorrow, we assume it's a forecast.
    assert get_target_filename('hfi20220824.tif') == 'sfms/uploads/forecast/2022-08-23/hfi20220824.tif'
