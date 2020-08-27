""" Mock modules/classes
"""
import logging
import os
import json
from urllib.parse import urlencode, urlsplit
from app import config, url_join
from app.tests.fixtures.loader import FixtureFinder


LOGGER = logging.getLogger(__name__)


class MockJWTDecode:
    """ Mock pyjwt module """

    @staticmethod
    def decode():
        """ Return something and don't raise any exception """
        return {}


class MockClientSession:
    """ Stubbed asyncronous context manager. """

    def __init__(self, json_response=None, text_response=None):
        """ Initialize client response """
        self.json_response = json_response
        self.text_response = text_response

    async def __aenter__(self):
        """ Enter context - return the appropriate response object depending on the url """
        if self.json_response:
            return MockAsyncResponse(json_response=self.json_response)
        return MockAsyncResponse(text_response=self.text_response)

    async def __aexit__(self, *error_info):
        """ Clean up anything you need to clean up """


class MockResponse:
    """ Stubbed response object. """

    def __init__(self, text: str = None, json_response: dict = None, status_code=200, content=None):
        """ Initialize client response """

        self.text = text
        self.content = content
        self.json_response = json_response
        self.status_code = status_code

    def json(self) -> dict:
        """ Return json response """
        return self.json_response


class MockAsyncResponse:
    """ Stubbed async response object.
    """

    def __init__(self, text_response: str = None, json_response: dict = None, status_code=200):
        """ Initialize client response """

        self.text_response = text_response
        self.json_response = json_response
        self.status_code = status_code

    async def text(self) -> str:
        """ Return text response """

        return self.text_response

    async def json(self) -> dict:
        """ Return json response """
        return self.json_response


def is_json(filename):
    extension = os.path.splitext(filename)[1]
    return extension == '.json'


def get_mock_client_session(url: str, params: dict = None) -> MockClientSession:
    """ Returns a mocked client session, looking for fixtures based on the url and params provided.
    """
    # Get the fixture filename
    fixture_finder = FixtureFinder()
    filename = fixture_finder.get_fixture_path(url, 'get', params)
    with open(filename) as fixture_file:
        if is_json(filename):
            return MockClientSession(json_response=json.load(fixture_file))
        else:
            return MockClientSession(text_response=fixture_file.read())


def default_mock_client_get(*args, **kwargs) -> MockClientSession:
    """ Return a mocked client session - this should be good for most request.
    """
    url = args[1]
    params = kwargs.get('params')
    return get_mock_client_session(url, params)


def _get_fixture_response(fixture):
    LOGGER.debug('construct response with {}'.format(fixture))
    with open(fixture) as fixture_file:
        if is_json(fixture):
            # Return a response with the appropriate fixture
            return MockResponse(json_response=json.load(fixture_file))
        else:
            # Return a response with the appropriate fixture
            return MockResponse(text=fixture_file.read())


def default_mock_requests_get(url, params=None, **kwargs) -> MockResponse:
    """ Return a mocked request response """
    # Get the file location of the fixture
    fixture_finder = FixtureFinder()
    filename = fixture_finder.get_fixture_path(url, 'get', params)
    # Construct the response
    return _get_fixture_response(filename)


def default_mock_requests_post(url, data, json, params=None, **kwargs) -> MockResponse:
    """ Return a mocked request response """
    # Get the file location of the fixture
    fixture_finder = FixtureFinder()
    filename = fixture_finder.get_fixture_path(url, 'post', params, data)
    # Construct the response
    return _get_fixture_response(filename)


def default_mock_requests_session_get(self, url, **kwargs) -> MockResponse:
    """ Return a mocked request response from a request.Session object """
    return default_mock_requests_get(url, **kwargs)


def default_mock_requests_session_post(self, url, data=None, json=None, **kwargs) -> MockResponse:
    """ Return a mocked request response from a request.Session object """
    return default_mock_requests_post(url, data, json, **kwargs)
