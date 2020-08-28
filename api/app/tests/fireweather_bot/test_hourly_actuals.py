""" Unit testing for hourly actuals bot (Marvin) """
import os
import logging
import requests
import pytest
from app.fireweather_bot import hourly_actuals
from app.tests.common import (default_mock_requests_session_get,
                              default_mock_requests_session_post, MockResponse)


logger = logging.getLogger(__name__)


@pytest.fixture()
def mock_requests_session(monkeypatch):
    """ Patch all calls to requests.Session.* """
    monkeypatch.setattr(requests.Session, 'get', default_mock_requests_session_get)
    monkeypatch.setattr(requests.Session, 'post', default_mock_requests_session_post)


def test_hourly_actuals_bot(mock_requests_session):
    """ Very simple (not very good) test that checks that the bot exits with a success code. """
    with pytest.raises(SystemExit) as excinfo:
        hourly_actuals.main()
    assert excinfo.value.code == 0
