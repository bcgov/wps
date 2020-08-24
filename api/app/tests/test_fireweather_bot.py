""" Unit tests for the fireweather bot """
import os
import logging
from requests import Session
import pytest
from alchemy_mock.mocking import UnifiedAlchemyMagicMock
import app.fireweather_bot_noon_forecasts

logger = logging.getLogger(__name__)


class MockResponse:
    """ Mock response object to fake out bot requests """

    def __init__(self, text=None, content=None):
        self.text = text
        self.content = content


@pytest.fixture()
def mock_request_session(monkeypatch):
    """ Mock out the request session object """

    # pylint: disable=unused-argument
    def mock_session_get(session, url: str, auth):
        """ Mock out calls to session.get """
        logger.debug('MOCK Session.get %s', url)
        if url.endswith('csv'):
            dirname = os.path.dirname(os.path.realpath(__file__))
            filename = os.path.join(dirname, 'test_fireweather_bot.csv')
            with open(filename, 'rb') as response_file:
                return MockResponse(content=response_file.read())
        return None

    def mock_session_post(session, url, data):
        """ Mock out calls to session.post """
        logger.debug('MOCK Session.post %s %s', url, data)
        dirname = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(dirname, 'test_fireweather_bot.html')
        with open(filename) as response_file:
            return MockResponse(text=response_file.read())

    monkeypatch.setattr(Session, 'get', mock_session_get)
    monkeypatch.setattr(Session, 'post', mock_session_post)


@pytest.fixture()
def mock_database_session(monkeypatch):
    """ Mock out the database session. """
    session = UnifiedAlchemyMagicMock()

    # pylint: disable=unused-argument
    def mock_get_session(*args):
        """ Return a mock database session """
        logger.info('MOCK database session')
        return session
    monkeypatch.setattr(app.db.database, 'get_session', mock_get_session)
    return session


# pylint: disable=redefined-outer-name, unused-argument
def test_fire_weather_bot(mock_request_session, mock_database_session):
    """ Very simple (not very good) test that checks that the bot exits with a success code. """
    with pytest.raises(SystemExit) as excinfo:
        app.fireweather_bot_noon_forecasts.main()
    assert excinfo.value.code == 0
