""" Global fixtures """

import logging
import pytest
from tests.common import MockJWTDecode

LOGGER = logging.getLogger(__name__)

# pylint: disable=unused-argument


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """ Automatically mock environment variable """

    monkeypatch.setenv("SPOTWX_BASE_URI",
                       "https://spotwx.com/services/api.php")
    monkeypatch.setenv("SPOTWX_API_KEY", "something")
    monkeypatch.setenv("USE_WFWX", 'False')
    monkeypatch.setenv("WFWX_USER", "user")
    monkeypatch.setenv("WFWX_SECRET", "secret")
    monkeypatch.setenv("WFWX_AUTH_URL", "http://localhost/token")
    monkeypatch.setenv("WFWX_BASE_URL", "http://localhost/page")
    monkeypatch.setenv("WFWX_MAX_PAGE_SIZE", "1000")
    monkeypatch.setenv("KEYCLOAK_PUBLIC_KEY", "public_key")


@pytest.fixture()
def mock_env_with_use_wfwx(monkeypatch):
    """ Set environment variable USE_WFWX to 'True' """

    monkeypatch.setenv("USE_WFWX", 'True')


@pytest.fixture
def mock_jwt_decode(monkeypatch):
    """ Mock pyjwt's decode method """

    def mock(*args, **kwargs):
        return MockJWTDecode()

    monkeypatch.setattr("jwt.decode", mock)
