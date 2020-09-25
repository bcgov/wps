""" Unit testing for hourly actuals bot (Marvin) """
import logging
import pytest
from app.fireweather_bot import hourly_actuals


logger = logging.getLogger(__name__)


def test_hourly_actuals_bot(mock_requests_session):  # pylint: disable=redefined-outer-name, unused-argument
    """ Very simple (not very good) test that checks that the bot exits with a success code. """
    with pytest.raises(SystemExit) as excinfo:
        hourly_actuals.main()
    assert excinfo.value.code == 0
