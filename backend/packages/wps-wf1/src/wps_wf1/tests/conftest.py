"""Global fixtures"""

from unittest.mock import MagicMock

import pytest
from aiohttp import ClientSession
from wps_wf1.cache_protocol import CacheProtocol
from wps_wf1.wfwx_settings import WfwxSettings


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Automatically mock environment variable"""
    monkeypatch.setenv("BASE_URI", "https://python-test-base-uri")
    monkeypatch.setenv("WFWX_USER", "user")
    monkeypatch.setenv("WFWX_SECRET", "secret")
    monkeypatch.setenv("WFWX_AUTH_URL", "https://wf1/pub/oauth2/v1/oauth/token")
    monkeypatch.setenv("WFWX_BASE_URL", "https://wf1/wfwx")
    monkeypatch.setenv("WFWX_MAX_PAGE_SIZE", "1000")


@pytest.fixture
def mock_session():
    """Mock ClientSession for unit tests"""
    return MagicMock(spec=ClientSession)


@pytest.fixture
def mock_settings():
    """Mock WfwxSettings for unit tests"""
    return WfwxSettings(
        base_url="https://test.example.com",
        auth_url="https://auth.example.com",
        user="test_user",
        secret="test_secret",
        max_page_size=100,
    )


@pytest.fixture
def mock_cache():
    """Mock CacheProtocol for unit tests"""
    return MagicMock(spec=CacheProtocol)
