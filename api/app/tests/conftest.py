""" Global fixtures """

from datetime import timezone, datetime
from contextlib import contextmanager
from typing import Generator
import logging
import requests
import pytest
from sqlalchemy.orm import Session
from alchemy_mock.mocking import UnifiedAlchemyMagicMock
from alchemy_mock.compat import mock
from pytest_mock import MockerFixture
import app.utils.s3
from app.utils.time import get_pst_tz
from app import auth
from app.tests.common import (
    MockJWTDecode, default_aiobotocore_get_session, default_mock_requests_get,
    default_mock_requests_post, default_mock_requests_session_get, default_mock_requests_session_post)
from app.db.models import PredictionModel, PredictionModelRunTimestamp
import app.db.database
import app.utils.time as time_utils
from app.schemas.shared import WeatherDataRequest

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """ Automatically mock environment variable """
    monkeypatch.setenv("BASE_URI", "https://python-test-base-uri")
    monkeypatch.setenv("USE_WFWX", "False")
    monkeypatch.setenv("WFWX_USER", "user")
    monkeypatch.setenv("WFWX_SECRET", "secret")
    monkeypatch.setenv(
        "WFWX_AUTH_URL", "https://wf1/pub/oauth2/v1/oauth/token")
    monkeypatch.setenv("WFWX_BASE_URL", "https://wf1/wfwx")
    monkeypatch.setenv("WFWX_MAX_PAGE_SIZE", "1000")
    monkeypatch.setenv("KEYCLOAK_PUBLIC_KEY", "public_key")
    monkeypatch.setenv("BC_FIRE_WEATHER_USER", "someuser")
    monkeypatch.setenv("BC_FIRE_WEATHER_SECRET", "password")
    monkeypatch.setenv("BC_FIRE_WEATHER_FILTER_ID", "1")
    monkeypatch.setenv("OPENSHIFT_BASE_URI",
                       "https://console.pathfinder.gov.bc.ca:8443")
    monkeypatch.setenv("PROJECT_NAMESPACE", "project_namespace")
    monkeypatch.setenv("STATUS_CHECKER_SECRET", "some_secret")
    monkeypatch.setenv("PATRONI_CLUSTER_NAME", "some_suffix")
    monkeypatch.setenv("ROCKET_URL_POST_MESSAGE",
                       "https://rc-notifications-test.ca/api/v1/chat.postMessage")
    monkeypatch.setenv("ROCKET_AUTH_TOKEN", "sometoken")
    monkeypatch.setenv("ROCKET_USER_ID", "someid")
    monkeypatch.setenv("ROCKET_CHANNEL", "#channel")
    monkeypatch.setenv("OPENSHIFT_NAMESPACE_API", "apis/apps/v1beta1/namespaces/")
    monkeypatch.setenv("OBJECT_STORE_SERVER", "some server")
    monkeypatch.setenv("OBJECT_STORE_USER_ID", "some user id")
    monkeypatch.setenv("OBJECT_STORE_SECRET", "some secret")
    monkeypatch.setenv("OBJECT_STORE_BUCKET", "some bucket")


@pytest.fixture(autouse=True)
def mock_aiobotocore_get_session(monkeypatch):
    """ Patch the session by default """
    monkeypatch.setattr(app.utils.s3, 'get_session', default_aiobotocore_get_session)


@pytest.fixture(autouse=True)
def mock_requests(monkeypatch):
    """ Patch all calls to request.get by default.
    """
    monkeypatch.setattr(requests, 'get', default_mock_requests_get)
    monkeypatch.setattr(requests, 'post', default_mock_requests_post)


@pytest.fixture(autouse=True)
def mock_get_now(monkeypatch):
    """ Patch all calls to app.timeutils: get_utc_now and get_pst_now  """
    timestamp = 1590076213962/1000

    # The default value for WeatherDataRequest cannot be mocked out, as it
    # is declared prior to test mocks being loaded. We manipulate the class
    # directly in order to have the desire default be deterministic.
    WeatherDataRequest.__fields__['time_of_interest'].default = datetime.fromtimestamp(
        timestamp, tz=timezone.utc)

    def mock_utc_now():
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)

    def mock_pst_now():
        return datetime.fromtimestamp(timestamp, tz=get_pst_tz())

    monkeypatch.setattr(app.utils.time, 'get_utc_now', mock_utc_now)
    monkeypatch.setattr(app.utils.time, 'get_pst_now', mock_pst_now)


@pytest.fixture(autouse=True)
def mock_session(monkeypatch):
    """ Ensure that all unit tests mock out the database session by default! """
    # pylint: disable=unused-argument

    @contextmanager
    def mock_get_session_scope(*args) -> Generator[Session, None, None]:
        """ return a session with a bare minimum database that should be good for most unit tests. """
        prediction_model = PredictionModel(id=1,
                                           abbreviation='GDPS',
                                           projection='latlon.15x.15',
                                           name='Global Deterministic Prediction System')
        prediction_model_run = PredictionModelRunTimestamp(
            id=1, prediction_model_id=1, prediction_run_timestamp=time_utils.get_utc_now(),
            prediction_model=prediction_model, complete=True)
        session = UnifiedAlchemyMagicMock(data=[
            (
                [mock.call.query(PredictionModel),
                 mock.call.filter(PredictionModel.abbreviation == 'GDPS',
                                  PredictionModel.projection == 'latlon.15x.15')],
                [prediction_model],
            ),
            (
                [mock.call.query(PredictionModelRunTimestamp)],
                [prediction_model_run]
            )
        ])
        yield session
    monkeypatch.setattr(app.db.database, 'get_read_session_scope', mock_get_session_scope)
    monkeypatch.setattr(app.db.database, 'get_write_session_scope', mock_get_session_scope)


@pytest.fixture()
def mock_env_with_use_wfwx(monkeypatch):
    """ Set environment variable USE_WFWX to 'True' """
    monkeypatch.setenv("USE_WFWX", 'True')


@pytest.fixture()
def mock_jwt_decode(monkeypatch):
    """ Mock pyjwt's decode method """

    # pylint: disable=unused-argument
    def mock_function(*args, **kwargs):
        return MockJWTDecode()

    monkeypatch.setattr("jwt.decode", mock_function)


@pytest.fixture()
def mock_requests_session(monkeypatch):
    """ Patch all calls to requests.Session.* """
    monkeypatch.setattr(requests.Session, 'get',
                        default_mock_requests_session_get)
    monkeypatch.setattr(requests.Session, 'post',
                        default_mock_requests_session_post)
    return monkeypatch


@pytest.fixture(autouse=True)
def spy_access_logging(mocker: MockerFixture):
    """Spies on access audting logging for tests"""
    return mocker.spy(auth, 'create_api_access_audit_log')
