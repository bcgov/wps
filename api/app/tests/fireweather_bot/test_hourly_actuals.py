""" Unit testing for hourly actuals bot (Marvin) """
import os
import logging
import requests
import pytest
from app.fireweather_bot import hourly_actuals
from app.tests.conftest import mock_requests_session


logger = logging.getLogger(__name__)


def test_hourly_actuals_bot(mock_requests_session):
    """ Very simple (not very good) test that checks that the bot exits with a success code. """
    with pytest.raises(SystemExit) as excinfo:
        hourly_actuals.main()
    assert excinfo.value.code == 0
