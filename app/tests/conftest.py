""" Global fixtures """

import logging
import pytest
from alchemy_mock.mocking import UnifiedAlchemyMagicMock
from app.tests.common import MockJWTDecode
import app.db.database

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
    monkeypatch.setenv(
        "WFWX_AUTH_URL", "http://localhost/pub/oauth2/v1/oauth/token")
    monkeypatch.setenv("WFWX_BASE_URL", "http://localhost/wfwx")
    monkeypatch.setenv("WFWX_MAX_PAGE_SIZE", "1000")
    monkeypatch.setenv("KEYCLOAK_PUBLIC_KEY", "public_key")


@pytest.fixture(autouse=True)
def mock_session(monkeypatch):
    """ Ensure that all unit tests mock out the database session by default! """
    def mock_get_session(*args):
        return UnifiedAlchemyMagicMock()
    monkeypatch.setattr(app.db.database, 'get_session', mock_get_session)


@pytest.fixture()
def mock_env_with_use_wfwx(monkeypatch):
    """ Set environment variable USE_WFWX to 'True' """

    monkeypatch.setenv("USE_WFWX", 'True')


@pytest.fixture()
def mock_env_with_use_spotwx(monkeypatch):
    """ Set environment variable USE_SPOTWX to 'True' """

    monkeypatch.setenv('USE_SPOTWX', 'True')


@pytest.fixture()
def mock_jwt_decode(monkeypatch):
    """ Mock pyjwt's decode method """

    def mock(*args, **kwargs):
        return MockJWTDecode()

    monkeypatch.setattr("jwt.decode", mock)
