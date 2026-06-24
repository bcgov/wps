"""Tests for wps_shared.weather_models.download"""
import tempfile
from unittest.mock import MagicMock

import pytest
import redis.exceptions
import requests

from wps_shared.tests.common import MockResponse
from wps_shared.weather_models import download


URL = "https://dd.weather.gc.ca/today/model_rdps/10km/00/001/some_file.grib2"
CACHE_VAR = "REDIS_CACHE_ENV_CANADA"
EXPIRY_VAR = "REDIS_ENV_CANADA_CACHE_EXPIRY"


@pytest.fixture
def mock_200_response():
    return MockResponse(content=b"grib data", status_code=200)


@pytest.fixture
def redis_down():
    """Redis client that raises ConnectionError on every call."""
    mock = MagicMock()
    mock.get.side_effect = redis.exceptions.ConnectionError("Connection refused")
    mock.set.side_effect = redis.exceptions.ConnectionError("Connection refused")
    return mock


@pytest.fixture
def redis_up_empty():
    """Redis client with no cached entry."""
    mock = MagicMock()
    mock.get.return_value = None
    return mock


class TestDownloadCacheDisabled:
    def test_downloads_file_when_cache_disabled(self, monkeypatch, mock_200_response):
        monkeypatch.setattr(requests, "get", lambda *_, **__: mock_200_response)
        with tempfile.TemporaryDirectory() as tmp:
            result = download(URL, tmp, CACHE_VAR, "RDPS")
        assert result is not None

    def test_returns_none_on_404_when_cache_disabled(self, monkeypatch):
        monkeypatch.setattr(requests, "get", lambda *_, **__: MockResponse(status_code=404))
        with tempfile.TemporaryDirectory() as tmp:
            result = download(URL, tmp, CACHE_VAR, "RDPS")
        assert result is None

    def test_raises_on_non_200_non_404(self, monkeypatch):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.raise_for_status.side_effect = requests.HTTPError()
        monkeypatch.setattr(requests, "get", lambda *_, **__: mock_resp)
        with tempfile.TemporaryDirectory() as tmp:
            with pytest.raises(requests.HTTPError):
                download(URL, tmp, CACHE_VAR, "RDPS")

    def test_gfs_filename_is_truncated(self, monkeypatch, mock_200_response):
        long_url = "https://example.com/" + "A" * 200 + ".grib2"
        monkeypatch.setattr(requests, "get", lambda *_, **__: mock_200_response)
        with tempfile.TemporaryDirectory() as tmp:
            result = download(long_url, tmp, CACHE_VAR, "GFS")
        assert result is not None
        assert len(result.split("/")[-1]) <= 81


class TestDownloadWithFetcher:
    def test_fetcher_success_returns_file(self, monkeypatch, mock_200_response):
        fetcher = MagicMock()
        fetcher.get.return_value = mock_200_response
        with tempfile.TemporaryDirectory() as tmp:
            result = download(URL, tmp, CACHE_VAR, "RDPS", fetcher=fetcher)
        assert result is not None
        fetcher.get.assert_called_once_with(URL)

    def test_fetcher_returns_none_means_all_404(self, monkeypatch):
        fetcher = MagicMock()
        fetcher.get.return_value = None
        with tempfile.TemporaryDirectory() as tmp:
            result = download(URL, tmp, CACHE_VAR, "RDPS", fetcher=fetcher)
        assert result is None


class TestDownloadCacheEnabled:
    def test_returns_cached_file_on_cache_hit(self, monkeypatch, mock_200_response):
        mock_redis = MagicMock()
        mock_redis.get.return_value = b"cached grib data"
        monkeypatch.setenv(CACHE_VAR, "True")
        monkeypatch.setattr("wps_shared.utils.redis._create_redis", lambda: mock_redis)
        with tempfile.TemporaryDirectory() as tmp:
            result = download(URL, tmp, CACHE_VAR, "RDPS")
        assert result is not None
        mock_redis.get.assert_called_once_with(URL)

    def test_downloads_and_caches_on_cache_miss(self, monkeypatch, mock_200_response, redis_up_empty):
        monkeypatch.setenv(CACHE_VAR, "True")
        monkeypatch.setattr("wps_shared.utils.redis._create_redis", lambda: redis_up_empty)
        monkeypatch.setattr(requests, "get", lambda *_, **__: mock_200_response)
        with tempfile.TemporaryDirectory() as tmp:
            result = download(URL, tmp, CACHE_VAR, "RDPS", EXPIRY_VAR)
        assert result is not None
        redis_up_empty.set.assert_called_once()

    def test_redis_get_failure_falls_through_to_download(self, monkeypatch, mock_200_response, redis_down, caplog):  # noqa: F811
        monkeypatch.setenv(CACHE_VAR, "True")
        monkeypatch.setattr("wps_shared.utils.redis._create_redis", lambda: redis_down)
        monkeypatch.setattr(requests, "get", lambda *_, **__: mock_200_response)
        with tempfile.TemporaryDirectory() as tmp:
            result = download(URL, tmp, CACHE_VAR, "RDPS")
        assert result is not None
        assert any("Connection refused" in r.message for r in caplog.records if r.levelname == "ERROR")

    def test_redis_set_failure_does_not_raise(self, monkeypatch, mock_200_response, redis_up_empty, caplog):
        """Redis being down during cache.set() must not propagate — this was the prod bug."""
        redis_up_empty.set.side_effect = redis.exceptions.ConnectionError("Connection refused")
        monkeypatch.setenv(CACHE_VAR, "True")
        monkeypatch.setattr("wps_shared.utils.redis._create_redis", lambda: redis_up_empty)
        monkeypatch.setattr(requests, "get", lambda *_, **__: mock_200_response)
        with tempfile.TemporaryDirectory() as tmp:
            result = download(URL, tmp, CACHE_VAR, "RDPS", EXPIRY_VAR)
        assert result is not None
        assert any("Connection refused" in r.message for r in caplog.records if r.levelname == "ERROR")
