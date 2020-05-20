""" Mock modules/classes
"""
import logging

LOGGER = logging.getLogger(__name__)

# pylint: disable=too-few-public-methods


class MockJWTDecode:
    """ Mock pyjwt module """

    @staticmethod
    def decode():
        """ Return something and don't raise any exception """
        return {}


class MockClientSession:
    """ Stubbed asyncronous context manager. """

    def __init__(self, json=None, text=None):
        """ Initialize client response """

        self.json = json
        self.text = text

    async def __aenter__(self):
        """ Enter context - return the appropriate response object depending on the url """

        if self.json:
            return MockResponse(json_response=self.json)
        return MockResponse(text_response=self.text)

    async def __aexit__(self, *error_info):
        """ Clean up anything you need to clean up """


class MockResponse:
    """ Stubbed response object.
    """

    def __init__(self, text_response=None, json_response=None):
        """ Initialize client response """

        self.text_response = text_response
        self.json_response = json_response

    async def text(self) -> str:
        """ Return text response """

        return self.text_response

    async def json(self) -> dict:
        """ Return json response """

        return self.json_response
