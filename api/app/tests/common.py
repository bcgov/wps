""" Mock modules/classes
"""
import logging
import os
import json
from urllib.parse import urlencode, urlsplit
from app import config, url_join


LOGGER = logging.getLogger(__name__)


class FixtureException(Exception):
    """ Exception for fixture related issues """


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

    def __init__(self, text_response: str = None, json_response: dict = None, status_code=200):
        """ Initialize client response """

        self.text_response = text_response
        self.json_response = json_response
        self.status_code = status_code

    def text(self) -> str:
        """ Return text response """

        return self.text_response

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


def _get_fixture_path(url: str, params: dict = None, auth=None) -> str:
    """ Returns the path to a fixture based on url and params.
    """
    # if config.get('WFWX_BASE_URL') in url:
    #     # Point to wf1 fixtures.
    #     fixture_url = 'wf1/' + url[len(config.get('WFWX_BASE_URL')):]
    # elif config.get('WFWX_AUTH_URL') in url:
    #     # Point to wf1 auth fixture.
    #     fixture_url = 'wf1/v1/oauth/token'
    # elif config.get('PATHFINDER_BASE_URI') in url:
    #     # Point to the pathfinder fixture url.
    #     fixture_url = 'pathfinder/' + \
    #         url[len(config.get('PATHFINDER_BASE_URI')):]
    # else:
    # Try to automatically find the fixture path
    fixture_url = urlsplit(url).netloc

    base_path = os.path.join(os.path.dirname(__file__), 'fixtures/', fixture_url)
    if not os.path.exists(base_path):
        raise FixtureException('unhandeled url: {}, fixture path ({}) does not exist'.format(url, base_path))

    print('auth: {}'.format(auth))

    if auth:
        fixture_url = url_join((fixture_url, 'auth'))

    if params:
        fixture_url = '{}?{}'.format(fixture_url, urlencode(params))
    # Join the url with the fixture location.
    return os.path.join(os.path.dirname(__file__), 'fixtures/', fixture_url)


def get_mock_client_session(url: str, params: dict = None) -> MockClientSession:
    """ Returns a mocked client session, looking for fixtures based on the url and params provided.
    """
    fixture = _get_fixture_path(url, params)
    LOGGER.debug('using fixture %s for %s', fixture, url)
    # We try looking for a json fixture 1st:
    if os.path.exists(fixture + '.json'):
        with open(fixture + '.json', 'r') as fixture_file:
            return MockClientSession(json_response=json.load(fixture_file))
    # No json fixture found, try a text file:
    elif os.path.exists(fixture + '.txt'):
        with open(fixture + '.txt', 'r') as fixture_file:
            return MockClientSession(text_response=fixture_file.read())
    # Expected fixture not found - raise an exception.
    raise FixtureException(
        'fixture file {} for {} not found.'.format(fixture, url))


def default_mock_client_get(*args, **kwargs) -> MockClientSession:
    """ Return a mocked client session - this should be good for most request.
    """
    url = args[1]
    params = kwargs.get('params')
    return get_mock_client_session(url, params)


def default_mock_requests_get(url, params=None, **kwargs) -> MockResponse:
    """ Return a mocked request response """
    auth = kwargs.get('auth')
    # Get the file location of the fixture
    fixture = _get_fixture_path(url, params, auth)
    # Try to get a matching json fixture
    if os.path.exists(fixture + '.json'):
        with open(fixture + '.json', 'r') as fixture_file:
            # Return a response with the appropriate fixture
            return MockResponse(json_response=json.load(fixture_file))
    # Expected fixture not found - raise an exception.
    raise FixtureException(
        'fixture file {} for {} not found.'.format(fixture, url))


def default_mock_session_requests_get(self, url, **kwargs) -> MockResponse:
    """ Return a mocked request response from a request.Session object """
    return default_mock_requests_get(url, **kwargs)
