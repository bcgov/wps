""" Global fixtures """

import datetime
from datetime import timezone
import logging
import requests
import pytest
from alchemy_mock.mocking import UnifiedAlchemyMagicMock
from alchemy_mock.compat import mock
from app.tests.common import MockJWTDecode, default_mock_requests_get
from app.db.models import PredictionModel, PredictionModelRunTimestamp
import app.db.database

LOGGER = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """ Automatically mock environment variable """
    monkeypatch.setenv("USE_WFWX", 'False')
    monkeypatch.setenv("WFWX_USER", "user")
    monkeypatch.setenv("WFWX_SECRET", "secret")
    monkeypatch.setenv(
        "WFWX_AUTH_URL", "http://localhost/pub/oauth2/v1/oauth/token")
    monkeypatch.setenv("WFWX_BASE_URL", "http://localhost/wfwx")
    monkeypatch.setenv("WFWX_MAX_PAGE_SIZE", "1000")
    monkeypatch.setenv("KEYCLOAK_PUBLIC_KEY", "public_key")
    monkeypatch.setenv("BC_FIRE_WEATHER_BASE_URL", "http://localhost")
    monkeypatch.setenv("BC_FIRE_WEATHER_USER", "someuser")
    monkeypatch.setenv("BC_FIRE_WEATHER_SECRET", "password")
    monkeypatch.setenv("BC_FIRE_WEATHER_FILTER_ID", "1")
    monkeypatch.setenv("PATHFINDER_BASE_URI",
                       "https://console.pathfinder.gov.bc.ca:8443")
    monkeypatch.setenv("PROJECT_NAMESPACE", "project_namespace")
    monkeypatch.setenv("STATUS_CHECKER_SECRET", "some_secret")
    monkeypatch.setenv("PATRONI_CLUSTER_NAME", "some_suffix")


@pytest.fixture(autouse=True)
def mock_requests(monkeypatch):
    """ Patch all calls to request.get by default.
    """
    monkeypatch.setattr(requests, 'get', default_mock_requests_get)


@pytest.fixture(autouse=True)
def mock_session(monkeypatch):
    """ Ensure that all unit tests mock out the database session by default! """
    # pylint: disable=unused-argument
    def mock_get_session(*args):
        """ return a session with a bare minimum database that should be good for most unit tests. """
        prediction_model = PredictionModel(id=1,
                                           abbreviation='GDPS',
                                           projection='latlon.15x.15',
                                           name='Global Deterministic Prediction System')
        preduction_model_run = PredictionModelRunTimestamp(id=1,
                                                           prediction_model_id=1,
                                                           prediction_run_timestamp=datetime.datetime.now(
                                                               tz=timezone.utc),
                                                           prediction_model=prediction_model)
        session = UnifiedAlchemyMagicMock(data=[
            (
                [mock.call.query(PredictionModel),
                 mock.call.filter(PredictionModel.abbreviation == 'GDPS',
                                  PredictionModel.projection == 'latlon.15x.15')],
                [prediction_model],
            ),
            (
                [mock.call.query(PredictionModelRunTimestamp)],
                [preduction_model_run]
            )
        ])
        return session
    monkeypatch.setattr(app.db.database, 'get_session', mock_get_session)


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
