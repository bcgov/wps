"""Unit tests for wfwx_client.py"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from urllib.parse import urlencode

import pytest
from wps_wf1.query_builders import BuildQuery
from wps_wf1.wfwx_client import WfwxClient, _cache_key


class MockAsyncContextManager:
    """Mock async context manager for aiohttp responses"""

    def __init__(self, response_data):
        self.response_data = response_data

    async def __aenter__(self):
        mock_response = AsyncMock()
        mock_response.json.return_value = self.response_data
        mock_response.raise_for_status.return_value = None
        return mock_response

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class TestCacheKey:
    """Test cases for the _cache_key function"""

    def test_cache_key_generation(self):
        """Test that cache key is generated correctly from URL and params"""
        url = "https://example.com/api/data"
        params = {"param1": "value1", "param2": "value2"}

        expected_key = f"{url}?{urlencode(params)}"
        result = _cache_key(url, params)

        assert result == expected_key

    def test_cache_key_with_empty_params(self):
        """Test cache key generation with empty parameters"""
        url = "https://example.com/api/data"
        params = {}

        expected_key = f"{url}?"
        result = _cache_key(url, params)

        assert result == expected_key

    def test_cache_key_with_special_characters(self):
        """Test cache key generation with special characters in parameters"""
        url = "https://example.com/api/data"
        params = {"query": "name=test&value=123", "filter": "active=true"}

        expected_key = f"{url}?{urlencode(params)}"
        result = _cache_key(url, params)

        assert result == expected_key


class TestWfwxClient:
    """Test cases for the WfwxClient class"""

    @pytest.fixture
    def wfwx_client(self, mock_session, mock_settings, mock_cache):
        """Create a WfwxClient instance with mocked dependencies"""
        return WfwxClient(mock_session, mock_settings, mock_cache)

    def test_init(self, mock_session, mock_settings, mock_cache):
        """Test WfwxClient initialization"""
        client = WfwxClient(mock_session, mock_settings, mock_cache)

        assert client.session == mock_session
        assert client.settings == mock_settings
        assert client.cache == mock_cache

    def test_init_without_cache(self, mock_session, mock_settings):
        """Test WfwxClient initialization without cache"""
        client = WfwxClient(mock_session, mock_settings)

        assert client.session == mock_session
        assert client.settings == mock_settings
        assert client.cache is None


class TestWfwxClientGetJson:
    """Test cases for the _get_json method"""

    @pytest.fixture
    def wfwx_client(self, mock_session, mock_settings, mock_cache):
        """Create a WfwxClient instance"""
        return WfwxClient(mock_session, mock_settings, mock_cache)

    @pytest.mark.anyio
    async def test_get_json_with_cache_hit(self, wfwx_client, mock_cache):
        """Test _get_json returns cached data when available"""
        url = "https://test.example.com/api/data"
        headers = {"Authorization": "Bearer token"}
        params = {"key": "value"}
        cached_data = {"cached": True}

        # Setup cache to return data
        mock_cache.get.return_value = json.dumps(cached_data).encode("utf-8")

        result = await wfwx_client._get_json(url, headers, params)

        assert result == cached_data
        # Verify cache was checked but no HTTP request was made
        mock_cache.get.assert_called_once()
        wfwx_client.session.get.assert_not_called()

    @pytest.mark.anyio
    async def test_get_json_with_cache_miss(self, wfwx_client, mock_cache):
        """Test _get_json fetches data when not cached"""
        url = "https://test.example.com/api/data"
        headers = {"Authorization": "Bearer token"}
        params = {"key": "value"}
        response_data = {"data": "test"}

        # Setup cache to return None (no cached data)
        mock_cache.get.return_value = None

        # Setup the session.get to return our mock context manager
        wfwx_client.session.get.return_value = MockAsyncContextManager(response_data)

        result = await wfwx_client._get_json(url, headers, params)

        assert result == response_data
        mock_cache.get.assert_called_once()
        # Verify the data was cached
        mock_cache.set.assert_called_once()

    @pytest.mark.anyio
    async def test_get_json_without_cache(self, mock_session, mock_settings):
        """Test _get_json when no cache is provided"""
        client = WfwxClient(mock_session, mock_settings)
        url = "https://test.example.com/api/data"
        headers = {"Authorization": "Bearer token"}
        params = {"key": "value"}
        response_data = {"data": "test"}

        # Setup the session.get to return our mock context manager
        mock_session.get.return_value = MockAsyncContextManager(response_data)

        result = await client._get_json(url, headers, params)

        assert result == response_data
        # Verify HTTP request was made
        mock_session.get.assert_called_once_with(url, headers=headers, params=params)

    @pytest.mark.anyio
    async def test_get_json_with_use_cache_false(self, wfwx_client, mock_cache):
        """Test _get_json respects use_cache=False parameter"""
        url = "https://test.example.com/api/data"
        headers = {"Authorization": "Bearer token"}
        params = {"key": "value"}
        response_data = {"data": "test"}

        # Setup the session.get to return our mock context manager
        wfwx_client.session.get.return_value = MockAsyncContextManager(response_data)

        result = await wfwx_client._get_json(url, headers, params, use_cache=False)

        assert result == response_data
        # Verify cache was not checked
        mock_cache.get.assert_not_called()

    @pytest.mark.anyio
    async def test_get_json_with_custom_ttl(self, wfwx_client, mock_cache):
        """Test _get_json uses custom TTL when provided"""
        url = "https://test.example.com/api/data"
        headers = {"Authorization": "Bearer token"}
        params = {"key": "value"}
        response_data = {"data": "test"}
        custom_ttl = 3600

        # Setup cache to return None (no cached data)
        mock_cache.get.return_value = None

        # Setup the session.get to return our mock context manager
        wfwx_client.session.get.return_value = MockAsyncContextManager(response_data)

        result = await wfwx_client._get_json(url, headers, params, ttl=custom_ttl)

        assert result == response_data
        # Verify the data was cached with custom TTL
        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args
        assert call_args[1]["ex"] == custom_ttl


class TestWfwxClientFetchAccessToken:
    """Test cases for the fetch_access_token method"""

    @pytest.fixture
    def wfwx_client(self, mock_session, mock_settings, mock_cache):
        """Create a WfwxClient instance"""
        return WfwxClient(mock_session, mock_settings, mock_cache)

    @pytest.mark.anyio
    async def test_fetch_access_token_with_cache_hit(self, wfwx_client, mock_cache):
        """Test fetch_access_token returns cached token when available"""
        cached_token = {"access_token": "cached_token", "expires_in": 3600}

        # Setup cache to return data
        mock_cache.get.return_value = json.dumps(cached_token).encode("utf-8")

        result = await wfwx_client.fetch_access_token(3600)

        assert result == cached_token
        mock_cache.get.assert_called_once()
        wfwx_client.session.get.assert_not_called()

    @pytest.mark.anyio
    async def test_fetch_access_token_with_cache_miss(self, wfwx_client, mock_cache):
        """Test fetch_access_token fetches new token when not cached"""
        token_response = {"access_token": "new_token", "expires_in": 7200}

        # Setup cache to return None (no cached data)
        mock_cache.get.return_value = None

        # Setup the session.get to return our mock context manager
        wfwx_client.session.get.return_value = MockAsyncContextManager(token_response)

        result = await wfwx_client.fetch_access_token(3600)

        assert result == token_response
        # Verify the token was cached with min(expires_in, ttl)
        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args
        assert call_args[1]["ex"] == 3600  # min(7200, 3600)

    @pytest.mark.anyio
    async def test_fetch_access_token_without_cache(self, mock_session, mock_settings):
        """Test fetch_access_token when no cache is provided"""
        client = WfwxClient(mock_session, mock_settings)
        token_response = {"access_token": "new_token", "expires_in": 3600}

        # Setup the session.get to return our mock context manager
        mock_session.get.return_value = MockAsyncContextManager(token_response)

        result = await client.fetch_access_token(3600)

        assert result == token_response
        # Verify HTTP request was made with correct auth
        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert call_args[1]["auth"].login == "test_user"
        assert call_args[1]["auth"].password == "test_secret"


class TestWfwxClientFetchPagedResponse:
    """Test cases for the fetch_paged_response_generator method"""

    @pytest.fixture
    def mock_query_builder(self):
        """Mock BuildQuery"""
        mock = MagicMock(spec=BuildQuery)
        return mock

    @pytest.fixture
    def wfwx_client(self, mock_session, mock_settings, mock_cache):
        """Create a WfwxClient instance"""
        return WfwxClient(mock_session, mock_settings, mock_cache)

    @pytest.mark.anyio
    async def test_fetch_paged_response_generator_single_page(
        self, wfwx_client, mock_query_builder
    ):
        """Test fetch_paged_response_generator with single page of results"""
        headers = {"Authorization": "Bearer token"}
        content_key = "items"

        # Setup query builder to return URL and params
        mock_query_builder.query.return_value = ("https://test.example.com/api/items", {"page": 0})

        # Setup response data
        response_data = {"page": {"totalPages": 1}, "_embedded": {"items": [{"id": 1}, {"id": 2}]}}

        # Mock _get_json to return response data
        wfwx_client._get_json = AsyncMock(return_value=response_data)

        # Test the generator
        results = []
        async for item in wfwx_client.fetch_paged_response_generator(
            headers, mock_query_builder, content_key
        ):
            results.append(item)

        assert len(results) == 2
        assert results[0] == {"id": 1}
        assert results[1] == {"id": 2}

    @pytest.mark.anyio
    async def test_fetch_paged_response_generator_multiple_pages(
        self, wfwx_client, mock_query_builder
    ):
        """Test fetch_paged_response_generator with multiple pages"""
        headers = {"Authorization": "Bearer token"}
        content_key = "items"

        # Setup query builder to return different URLs for each page
        mock_query_builder.query.side_effect = [
            ("https://test.example.com/api/items", {"page": 0}),
            ("https://test.example.com/api/items", {"page": 1}),
            ("https://test.example.com/api/items", {"page": 2}),
        ]

        # Setup response data for each page
        response_data_page_0 = {
            "page": {"totalPages": 3},
            "_embedded": {"items": [{"id": 1}, {"id": 2}]},
        }
        response_data_page_1 = {
            "page": {"totalPages": 3},
            "_embedded": {"items": [{"id": 3}, {"id": 4}]},
        }
        response_data_page_2 = {"page": {"totalPages": 3}, "_embedded": {"items": [{"id": 5}]}}

        # Setup the session.get to return different responses for each call
        wfwx_client.session.get.side_effect = [
            MockAsyncContextManager(response_data_page_0),
            MockAsyncContextManager(response_data_page_1),
            MockAsyncContextManager(response_data_page_2),
        ]

        # Test the generator
        results = []
        async for item in wfwx_client.fetch_paged_response_generator(
            headers, mock_query_builder, content_key
        ):
            results.append(item)

        assert len(results) == 5
        assert results == [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}]


class TestWfwxClientFetchRawDailies:
    """Test cases for the fetch_raw_dailies_for_all_stations method"""

    @pytest.fixture
    def wfwx_client(self, mock_session, mock_settings):
        """Create a WfwxClient instance"""
        return WfwxClient(mock_session, mock_settings)

    @pytest.mark.anyio
    async def test_fetch_raw_dailies_single_page(self, wfwx_client):
        """Test fetch_raw_dailies_for_all_stations with single page"""
        headers = {"Authorization": "Bearer token"}
        time_of_interest = datetime(2023, 1, 1, 12, 0, 0)
        timestamp = int(time_of_interest.timestamp() * 1000)

        # Setup response data
        response_data = {
            "page": {"totalPages": 1},
            "_embedded": {"dailies": [{"id": 1, "temp": 20}, {"id": 2, "temp": 22}]},
        }

        # Setup the session.get to return our mock context manager
        wfwx_client.session.get.return_value = MockAsyncContextManager(response_data)

        result = await wfwx_client.fetch_raw_dailies_for_all_stations(headers, time_of_interest)

        assert len(result) == 2
        assert result[0] == {"id": 1, "temp": 20}
        assert result[1] == {"id": 2, "temp": 22}

        # Verify the correct URL and parameters were used
        expected_url = f"{wfwx_client.settings.base_url}/v1/dailies/rsql"
        expected_params = {
            "query": f"weatherTimestamp=={timestamp}",
            "page": 0,
            "size": wfwx_client.settings.max_page_size,
        }

        wfwx_client.session.get.assert_called_once_with(
            expected_url, params=expected_params, headers=headers
        )

    @pytest.mark.anyio
    async def test_fetch_raw_dailies_multiple_pages(self, wfwx_client):
        """Test fetch_raw_dailies_for_all_stations with multiple pages"""
        headers = {"Authorization": "Bearer token"}
        time_of_interest = datetime(2023, 1, 1, 12, 0, 0)

        # Setup response data for multiple pages
        response_data_page_0 = {"page": {"totalPages": 2}, "_embedded": {"dailies": [{"id": 1}]}}
        response_data_page_1 = {
            "page": {"totalPages": 2},
            "_embedded": {"dailies": [{"id": 2}, {"id": 3}]},
        }

        # Setup the session.get to return different responses for each call
        wfwx_client.session.get.side_effect = [
            MockAsyncContextManager(response_data_page_0),
            MockAsyncContextManager(response_data_page_1),
        ]

        result = await wfwx_client.fetch_raw_dailies_for_all_stations(headers, time_of_interest)

        assert len(result) == 3
        assert result == [{"id": 1}, {"id": 2}, {"id": 3}]


class TestWfwxClientFetchHourlies:
    """Test cases for hourlies-related methods"""

    @pytest.fixture
    def wfwx_client(self, mock_session, mock_settings, mock_cache):
        """Create a WfwxClient instance"""
        return WfwxClient(mock_session, mock_settings, mock_cache)

    def test_prepare_fetch_hourlies_query(self, wfwx_client):
        """Test prepare_fetch_hourlies_query generates correct URL and parameters"""
        raw_station = {"id": "station123"}
        start_datetime = datetime(2023, 1, 1, 0, 0, 0)
        end_datetime = datetime(2023, 1, 1, 23, 59, 59)

        start_ts = int(start_datetime.timestamp() * 1000)
        end_ts = int(end_datetime.timestamp() * 1000)

        url, params = wfwx_client.prepare_fetch_hourlies_query(
            raw_station, start_datetime, end_datetime
        )

        expected_url = f"{wfwx_client.settings.base_url}/v1/hourlies/search/findHourliesByWeatherTimestampBetweenAndStationIdEqualsOrderByWeatherTimestampAsc"
        expected_params = {
            "startTimestamp": start_ts,
            "endTimestamp": end_ts,
            "stationId": "station123",
        }

        assert url == expected_url
        assert params == expected_params

    @pytest.mark.anyio
    async def test_fetch_hourlies(self, wfwx_client):
        """Test fetch_hourlies calls _get_json with correct parameters"""
        raw_station = {"id": "station123"}
        headers = {"Authorization": "Bearer token"}
        start_datetime = datetime(2023, 1, 1, 0, 0, 0)
        end_datetime = datetime(2023, 1, 1, 23, 59, 59)
        use_cache = True
        ttl = 3600

        response_data = {"hourlies": [{"temp": 20}, {"temp": 22}]}
        wfwx_client._get_json = AsyncMock(return_value=response_data)

        result = await wfwx_client.fetch_hourlies(
            raw_station, headers, start_datetime, end_datetime, use_cache, ttl
        )

        assert result == response_data
        wfwx_client._get_json.assert_called_once()


class TestWfwxClientFetchStations:
    """Test cases for the fetch_stations_by_group_id method"""

    @pytest.fixture
    def wfwx_client(self, mock_session, mock_settings):
        """Create a WfwxClient instance"""
        return WfwxClient(mock_session, mock_settings)

    @pytest.mark.anyio
    async def test_fetch_stations_by_group_id(self, wfwx_client):
        """Test fetch_stations_by_group_id fetches stations for a group"""
        headers = {"Authorization": "Bearer token"}
        group_id = "group123"
        response_data = {"_embedded": {"stations": [{"id": 1}, {"id": 2}]}}

        # Setup the session.get to return our mock context manager
        wfwx_client.session.get.return_value = MockAsyncContextManager(response_data)

        result = await wfwx_client.fetch_stations_by_group_id(headers, group_id)

        assert result == response_data

        # Verify the correct URL was used
        expected_url = f"{wfwx_client.settings.base_url}/v1/stationGroups/{group_id}/members"
        wfwx_client.session.get.assert_called_once_with(expected_url, headers=headers)
