""" Unit tests for the fireweather noon forecats bot (Bender) """
import os
import logging
import requests
import pytest
import app
from app.tests.common import (default_mock_requests_session_get,
                              default_mock_requests_session_post)
from app.fireweather_bot import noon_forecasts

logger = logging.getLogger(__name__)


# @pytest.fixture()
# def mock_request_session(monkeypatch):
#     """ Mock out the request session object """

#     # pylint: disable=unused-argument
#     def mock_session_get(session, url: str, auth):
#         """ Mock out calls to session.get """
#         logger.debug('MOCK Session.get %s', url)
#         if url.endswith('csv'):
#             dirname = os.path.dirname(os.path.realpath(__file__))
#             filename = os.path.join(dirname, 'test_noon_forecasts.csv')
#             with open(filename, 'rb') as response_file:
#                 return MockResponse(content=response_file.read())
#         return None

#     def mock_session_post(session, url, data):
#         """ Mock out calls to session.post """
#         logger.debug('MOCK Session.post %s %s', url, data)
#         dirname = os.path.dirname(os.path.realpath(__file__))
#         filename = os.path.join(dirname, 'test_noon_forecasts.html')
#         with open(filename) as response_file:
#             return MockResponse(text=response_file.read())

#     monkeypatch.setattr(Session, 'get', mock_session_get)
#     monkeypatch.setattr(Session, 'post', mock_session_post)


@pytest.fixture()
def mock_requests_session(monkeypatch):
    """ Patch all calls to requests.Session.* """
    monkeypatch.setattr(requests.Session, 'get', default_mock_requests_session_get)
    monkeypatch.setattr(requests.Session, 'post', default_mock_requests_session_post)

# pylint: disable=redefined-outer-name, unused-argument


def test_noon_forecasts_bot(mock_requests_session):
    """ Very simple (not very good) test that checks that the bot exits with a success code. """
    with pytest.raises(SystemExit) as excinfo:
        noon_forecasts.main()
    assert excinfo.value.code == 0
