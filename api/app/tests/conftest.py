"""Global fixtures"""

from datetime import timezone, datetime
import logging
from typing import Optional
from aiohttp import ClientSession
from unittest.mock import MagicMock
import requests
import pytest
from pytest_mock import MockerFixture
from wps_shared.db.models.weather_models import PredictionModel, PredictionModelRunTimestamp
import wps_shared.utils.s3
from wps_shared.utils.time import get_pst_tz, get_utc_now
import wps_shared.utils.time
from app import auth
from app.tests.common import (
    MockJWTDecode,
    default_aiobotocore_get_session,
    default_mock_requests_get,
    default_mock_requests_post,
    default_mock_client_get,
    default_mock_requests_session_get,
    default_mock_requests_session_post,
)
import wps_shared.db.database
from wps_shared.weather_models import ModelEnum, ProjectionEnum
import wps_jobs.wps_jobs.weather_model_jobs.env_canada
import wps_jobs.wps_jobs.weather_model_jobs.utils.process_grib
from wps_shared.schemas.shared import WeatherDataRequest
import wps_shared.wildfire_one.wildfire_fetchers
import wps_shared.utils.redis

logger = logging.getLogger(__name__)


@pytest.fixture
def anyio_backend():
    """Specifies asyncio as the anyio backend"""
    return "asyncio"


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Automatically mock environment variable"""
    monkeypatch.setenv("BASE_URI", "https://python-test-base-uri")
    monkeypatch.setenv("WFWX_USER", "user")
    monkeypatch.setenv("WFWX_SECRET", "secret")
    monkeypatch.setenv("WFWX_AUTH_URL", "https://wf1/pub/oauth2/v1/oauth/token")
    monkeypatch.setenv("WFWX_BASE_URL", "https://wf1/wfwx")
    monkeypatch.setenv("WFWX_MAX_PAGE_SIZE", "1000")
    monkeypatch.setenv("KEYCLOAK_PUBLIC_KEY", "public_key")
    monkeypatch.setenv("OPENSHIFT_BASE_URI", "https://console.pathfinder.gov.bc.ca:8443")
    monkeypatch.setenv("PROJECT_NAMESPACE", "project_namespace")
    monkeypatch.setenv("STATUS_CHECKER_SECRET", "some_secret")
    monkeypatch.setenv("PATRONI_CLUSTER_NAME", "some_suffix")
    monkeypatch.setenv("ROCKET_URL_POST_MESSAGE", "https://rc-notifications-test.ca/api/v1/chat.postMessage")
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
    """Patch the session by default"""
    monkeypatch.setattr(wps_shared.utils.s3, "get_session", default_aiobotocore_get_session)


@pytest.fixture(autouse=True)
def mock_requests(monkeypatch):
    """Patch all calls to request.get by default."""
    monkeypatch.setattr(requests, "get", default_mock_requests_get)
    monkeypatch.setattr(requests, "post", default_mock_requests_post)


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    """Patch redis by default"""

    class MockRedis:
        """mocked redis class"""

        def __init__(self) -> None:
            """Mock init"""

        def get(self, name):
            """mock get"""
            return None

        def set(self, name, value, ex=None, px=None, nx=False, xx=False, keepttl=False):
            """mock set"""

        def delete(self, name):
            """mock delete"""

    def create_mock_redis():
        return MockRedis()

    monkeypatch.setattr(wps_shared.utils.redis, "_create_redis", create_mock_redis)


@pytest.fixture(autouse=True)
def mock_get_now(monkeypatch):
    """Patch all calls to wps_shared.util.time: get_utc_now and get_pst_now"""
    # May 21, 2020
    timestamp = 1590076213962 / 1000

    # The default value for WeatherDataRequest cannot be mocked out, as it
    # is declared prior to test mocks being loaded. We manipulate the class
    # directly in order to have the desire default be deterministic.
    WeatherDataRequest.__fields__["time_of_interest"].default = datetime.fromtimestamp(timestamp, tz=timezone.utc)

    def mock_utc_now():
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)

    def mock_pst_now():
        return datetime.fromtimestamp(timestamp, tz=get_pst_tz())

    monkeypatch.setattr(wps_shared.utils.time, "_get_utc_now", mock_utc_now)
    monkeypatch.setattr(wps_shared.utils.time, "_get_pst_now", mock_pst_now)


@pytest.fixture(autouse=True)
def mock_get_pst_today_start_and_end(monkeypatch):
    """Patch all calls to app.util.time: get_pst_today_start_and_end"""

    def mock_get_pst_today():
        start = datetime.fromtimestamp(1623974400, tz=get_pst_tz())
        end = datetime.fromtimestamp(1624060800, tz=get_pst_tz())
        return start, end

    monkeypatch.setattr(wps_shared.utils.time, "get_pst_today_start_and_end", mock_get_pst_today)


@pytest.fixture(autouse=True)
def mock_session(monkeypatch):
    """Ensure that all unit tests mock out the database session by default!"""
    monkeypatch.setattr(wps_shared.db.database, "_get_write_session", MagicMock())
    monkeypatch.setattr(wps_shared.db.database, "_get_read_session", MagicMock())

    prediction_model = PredictionModel(id=1, abbreviation="GDPS", projection="latlon.15x.15", name="Global Deterministic Prediction System")

    def mock_get_prediction_model(session, model, projection) -> Optional[PredictionModel]:
        if model == ModelEnum.GDPS and projection == ProjectionEnum.LATLON_15X_15:
            return prediction_model
        return None

    def mock_get_prediction_run(session, prediction_model_id: int, prediction_run_timestamp: datetime):
        return PredictionModelRunTimestamp(id=1, prediction_model_id=1, prediction_run_timestamp=get_utc_now(), prediction_model=prediction_model, complete=True)

    monkeypatch.setattr(wps_jobs.wps_jobs.weather_model_jobs.env_canada, "get_prediction_model", mock_get_prediction_model)
    monkeypatch.setattr(wps_jobs.wps_jobs.weather_models.process_grib, "get_prediction_model", mock_get_prediction_model)
    monkeypatch.setattr(wps_jobs.wps_jobs.weather_model_jobs.env_canada, "get_prediction_run", mock_get_prediction_run)


@pytest.fixture()
def mock_jwt_decode(monkeypatch):
    """Mock pyjwt's decode method"""

    def mock_function(*args, **kwargs):
        return MockJWTDecode()

    monkeypatch.setattr("jwt.decode", mock_function)


@pytest.fixture(autouse=True)
def mock_sentry(monkeypatch):
    """Mock sentrys' set_user function"""

    def mock_sentry(*args, **kwargs):
        """No-op"""
        pass

    monkeypatch.setattr("app.auth.set_user", mock_sentry)


@pytest.fixture()
def mock_requests_session(monkeypatch):
    """Patch all calls to requests.Session.*"""
    monkeypatch.setattr(requests.Session, "get", default_mock_requests_session_get)
    monkeypatch.setattr(requests.Session, "post", default_mock_requests_session_post)
    return monkeypatch


@pytest.fixture()
def mock_client_session(monkeypatch):
    """Patch all calls to aiohttp.ClientSession"""
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    monkeypatch.setattr(ClientSession, "post", default_mock_client_get)
    return monkeypatch


@pytest.fixture(autouse=True)
def spy_access_logging(mocker: MockerFixture):
    """Spies on access audting logging for tests"""
    return mocker.spy(auth, "create_api_access_audit_log")
