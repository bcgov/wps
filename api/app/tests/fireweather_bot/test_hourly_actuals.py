""" Unit testing for hourly actuals bot (Marvin) """
import pytest
from app.fireweather_bot import hourly_actuals


def test_hourly_actuals_bot():
    """ Very simple (not very good) test that checks that the bot exits with a success code. """
    with pytest.raises(SystemExit) as excinfo:
        hourly_actuals.main()
    assert excinfo.value.code == 0
