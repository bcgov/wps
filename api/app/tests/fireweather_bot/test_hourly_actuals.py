""" Unit testing for hourly actuals bot (Marvin) """
import os
import logging
import requests
import pytest
from app.fireweather_bot import hourly_actuals
from app.tests.common import default_mock_requests_session_get, MockResponse


logger = logging.getLogger(__name__)


@pytest.fixture()
def mock_requests_session(monkeypatch):
    """ Patch all calls to requests.Session.* """

    def mock_session_post(session, url, data):
        """ Mock out calls to session.post """
        logger.debug('MOCK Session.post %s %s', url, data)
        dirname = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(dirname, 'test_hourly_actuals.html')
        with open(filename) as response_file:
            return MockResponse(text=response_file.read())

    monkeypatch.setattr(requests.Session, 'get', default_mock_requests_session_get)
    monkeypatch.setattr(requests.Session, 'post', mock_session_post)


def test_hourly_actuals_bot(mock_requests_session):
    """ Very simple (not very good) test that checks that the bot exits with a success code. """
    with pytest.raises(SystemExit) as excinfo:
        hourly_actuals.main()
    assert excinfo.value.code == 0
