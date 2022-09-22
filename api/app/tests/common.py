""" Mock modules/classes
"""
import logging
import os
import json
from typing import Optional
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class MockJWTDecode:
    """ Mock pyjwt module """

    def __init__(self):
        self.decoded_token = {"idir_username": "test_username"}

    def __getitem__(self, key):
        return self.decoded_token[key]

    def get(self, key, _):
        "Returns the mock decoded token"
        return self.decoded_token.get(key, {})

    def decode(self):
        "Returns the mock decoded token"
        return self.decoded_token


class MockClientSession:
    """ Stubbed asyncronous context manager. """

    # pylint: disable=redefined-outer-name
    def __init__(self, json=None, text=None):
        """ Initialize client response """
        self._json = json
        self._text = text

    async def __aenter__(self):
        """ Enter context - return the appropriate response object depending on the url """
        if self._json:
            return MockAsyncResponse(json=self._json)
        return MockAsyncResponse(text=self._text)

    async def __aexit__(self, *error_info):
        """ Clean up anything you need to clean up """


class MockResponse:
    """ Stubbed response object. """

    # pylint: disable=redefined-outer-name
    def __init__(self, text: str = None, json: dict = None, status_code=200, content=None):
        """ Initialize client response """

        self.text = text
        self.content = content
        self._json = json
        self.status_code = status_code

    def json(self) -> dict:
        """ Return json response """
        return self._json


class MockAsyncResponse:
    """ Stubbed async response object.
    """

    # pylint: disable=redefined-outer-name
    def __init__(self, text: str = None, json: dict = None, status_code=200):
        """ Initialize client response """
        self._text = text
        self._json = json
        # NOTE: there is no status_code response!
        # self.status_code = status_code
        self.status = status_code

    async def text(self) -> str:
        """ Return text response """

        return self._text

    async def json(self) -> dict:
        """ Return json response """
        return self._json


class DefaultMockAioSession:
    """ Mock aiobotocore.session.AioSession """
    # pylint: disable=unused-argument

    @asynccontextmanager
    async def create_client(self, *args, **kwargs):
        """ Mock create client """
        yield DefaultMockAioBaseClient()


class DefaultMockAioBaseClient:
    """ Stubbed AioBaseClient object
    """
    # It's a stubbed object, so we don't care about pylint warnings:
    # pylint: disable=unused-argument, missing-function-docstring, too-many-arguments

    def __init__(self, *args, **kwargs):
        """ you can set the values below for some default behaviour """
        self.mock_generate_presigned_url: Optional[str] = None
        self.mock_list_objects_v2_lookup: dict = {}

    async def list_objects_v2(self, *args, **kwargs) -> dict:
        """ mock list objects """
        if kwargs.get('Prefix') in self.mock_list_objects_v2_lookup:
            return self.mock_list_objects_v2_lookup[kwargs.get('Prefix')]
        raise NotImplementedError(f"no lookup for {kwargs.get('Prefix')}")

    async def put_object(self, *args, **kwargs) -> dict:
        """ mock put object """

    async def generate_presigned_url(self, *args, **kwargs) -> str:
        """ mock presigned url """
        return self.mock_generate_presigned_url

    async def __aenter__(self):
        """ Enter context """

    async def __aexit__(self, *error_info):
        """ Clean up anything you need to clean up """

    async def close(self, *args, **kwargs):
        """Close all http connections."""


def default_aiobotocore_get_session():
    """ Default session stub """
    return DefaultMockAioSession()


def is_json(filename):
    """ Check if file is a json file (look if the extension is .json) """
    extension = os.path.splitext(filename)[1]
    return extension == '.json'


def _get_fixture_response(fixture):
    logger.debug('construct response with %s', fixture)
    with open(fixture, 'rb') as fixture_file:
        if is_json(fixture):
            # Return a response with the appropriate fixture
            return MockResponse(json=json.load(fixture_file))
        # Return a response with the appropriate fixture
        data = fixture_file.read()
        return MockResponse(text=data.decode(), content=data)


def str2float(value: str):
    """ Change a string into a floating point number, or a None """
    if value == 'None':
        return None
    return float(value)
