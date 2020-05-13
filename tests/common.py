""" Code common to tests
"""
import logging

LOGGER = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class ClientResponse:
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


class ResponseAsyncContextManagerBase:
    """ Stubbed asyncronous context manager.
    """

    def __init__(self, url):
        """ Remember the url so that we can change our response depending on the request.
        """
        self.url = url

    async def __aenter__(self):
        """ Enter context - return the appropriate response object depending on the url
        """
        if 'token' in self.url:
            return ClientResponse(json_response={'access_token': 'token'})
        raise Exception('unexpected url: {}'.format(self.url))

    # pylint: disable=invalid-name
    async def __aexit__(self, exc_type, exc, tb):
        """ Exit context
        """
