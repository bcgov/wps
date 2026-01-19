"""Unit tests for SFMS common utilities."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.sfms.sfms_common import fetch_station_actuals
from wps_shared.schemas.stations import WeatherStation
from wps_shared.schemas.sfms import SFMSDailyActual


def create_test_station(code: int, lat: float, lon: float, elevation: int | None = 100) -> WeatherStation:
    """Create a test weather station."""
    return WeatherStation(
        code=code,
        name=f"Station {code}",
        lat=lat,
        long=lon,
        elevation=elevation,
    )


def create_raw_daily(
    station_code: int,
    record_type: str = "ACTUAL",
    temperature: float = 20.0,
    station_status: str = "ACTIVE",
) -> dict:
    """Create a mock raw daily record from WF1 API."""
    return {
        "stationData": {
            "stationCode": station_code,
            "stationStatus": {"id": station_status},
            "latitude": 49.0,
            "longitude": -123.0,
        },
        "recordType": {"id": record_type},
        "temperature": temperature,
        "relativeHumidity": 50.0,
        "precipitation": 0.0,
        "windSpeed": 10.0,
    }


class TestFetchStationActuals:
    """Tests for fetch_station_actuals function."""

    @pytest.mark.anyio
    async def test_returns_actuals_for_valid_stations(self):
        """Test that valid stations with ACTUAL records are returned."""
        session = AsyncMock()
        headers = {"Authorization": "Bearer token"}
        time_of_interest = datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
        stations = [
            create_test_station(100, 49.0, -123.0),
            create_test_station(101, 50.0, -124.0),
        ]

        raw_dailies = [
            create_raw_daily(100, temperature=15.0),
            create_raw_daily(101, temperature=18.0),
        ]

        with patch("app.sfms.sfms_common.fetch_raw_dailies_for_all_stations", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = raw_dailies

            result = await fetch_station_actuals(session, headers, time_of_interest, stations)

        assert len(result) == 2
        assert all(isinstance(r, SFMSDailyActual) for r in result)
        assert result[0].code == 100
        assert result[0].temperature == pytest.approx(15.0)
        assert result[1].code == 101
        assert result[1].temperature == pytest.approx(18.0)

    @pytest.mark.anyio
    async def test_filters_non_actual_records(self):
        """Test that non-ACTUAL records are filtered out."""
        session = AsyncMock()
        headers = {}
        time_of_interest = datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
        stations = [create_test_station(100, 49.0, -123.0)]

        raw_dailies = [
            create_raw_daily(100, record_type="FORECAST"),
            create_raw_daily(100, record_type="ACTUAL"),
        ]

        with patch("app.sfms.sfms_common.fetch_raw_dailies_for_all_stations", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = raw_dailies

            result = await fetch_station_actuals(session, headers, time_of_interest, stations)

        assert len(result) == 1

    @pytest.mark.anyio
    async def test_filters_stations_not_in_lookup(self):
        """Test that stations not in the provided list are filtered out."""
        session = AsyncMock()
        headers = {}
        time_of_interest = datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
        stations = [create_test_station(100, 49.0, -123.0)]

        raw_dailies = [
            create_raw_daily(100),
            create_raw_daily(999),  # Not in stations list
        ]

        with patch("app.sfms.sfms_common.fetch_raw_dailies_for_all_stations", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = raw_dailies

            result = await fetch_station_actuals(session, headers, time_of_interest, stations)

        assert len(result) == 1
        assert result[0].code == 100

    @pytest.mark.anyio
    async def test_filters_invalid_stations(self):
        """Test that invalid stations (non-ACTIVE/TEST/PROJECT status) are filtered out."""
        session = AsyncMock()
        headers = {}
        time_of_interest = datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
        stations = [
            create_test_station(100, 49.0, -123.0),
            create_test_station(101, 50.0, -124.0),
        ]

        raw_dailies = [
            create_raw_daily(100, station_status="ACTIVE"),
            create_raw_daily(101, station_status="INACTIVE"),  # Invalid status
        ]

        with patch("app.sfms.sfms_common.fetch_raw_dailies_for_all_stations", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = raw_dailies

            result = await fetch_station_actuals(session, headers, time_of_interest, stations)

        assert len(result) == 1
        assert result[0].code == 100

    @pytest.mark.anyio
    async def test_require_elevation_filters_stations_without_elevation(self):
        """Test that stations without elevation are filtered when require_elevation=True."""
        session = AsyncMock()
        headers = {}
        time_of_interest = datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
        stations = [
            create_test_station(100, 49.0, -123.0, elevation=500),
            create_test_station(101, 50.0, -124.0, elevation=None),
        ]

        raw_dailies = [
            create_raw_daily(100),
            create_raw_daily(101),
        ]

        with patch("app.sfms.sfms_common.fetch_raw_dailies_for_all_stations", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = raw_dailies

            result = await fetch_station_actuals(session, headers, time_of_interest, stations, require_elevation=True)

        assert len(result) == 1
        assert result[0].code == 100

    @pytest.mark.anyio
    async def test_require_elevation_false_includes_stations_without_elevation(self):
        """Test that stations without elevation are included when require_elevation=False."""
        session = AsyncMock()
        headers = {}
        time_of_interest = datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
        stations = [
            create_test_station(100, 49.0, -123.0, elevation=None),
        ]

        raw_dailies = [create_raw_daily(100)]

        with patch("app.sfms.sfms_common.fetch_raw_dailies_for_all_stations", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = raw_dailies

            result = await fetch_station_actuals(session, headers, time_of_interest, stations, require_elevation=False)

        assert len(result) == 1

    @pytest.mark.anyio
    async def test_empty_raw_dailies_returns_empty_list(self):
        """Test that empty raw dailies returns empty list."""
        session = AsyncMock()
        headers = {}
        time_of_interest = datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
        stations = [create_test_station(100, 49.0, -123.0)]

        with patch("app.sfms.sfms_common.fetch_raw_dailies_for_all_stations", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []

            result = await fetch_station_actuals(session, headers, time_of_interest, stations)

        assert result == []

    @pytest.mark.anyio
    async def test_continues_processing_on_exception(self):
        """Test that processing continues when an exception occurs for one record."""
        session = AsyncMock()
        headers = {}
        time_of_interest = datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
        stations = [
            create_test_station(100, 49.0, -123.0),
            create_test_station(101, 50.0, -124.0),
        ]

        raw_dailies = [
            None,  # Will cause an exception
            create_raw_daily(101),
        ]

        with patch("app.sfms.sfms_common.fetch_raw_dailies_for_all_stations", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = raw_dailies

            result = await fetch_station_actuals(session, headers, time_of_interest, stations)

        # Should still return the valid record
        assert len(result) == 1
        assert result[0].code == 101

    @pytest.mark.anyio
    async def test_maps_station_coordinates_correctly(self):
        """Test that station lat/lon are correctly mapped to the result."""
        session = AsyncMock()
        headers = {}
        time_of_interest = datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
        stations = [create_test_station(100, 49.5, -123.5, elevation=750)]

        raw_dailies = [create_raw_daily(100, temperature=22.5)]

        with patch("app.sfms.sfms_common.fetch_raw_dailies_for_all_stations", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = raw_dailies

            result = await fetch_station_actuals(session, headers, time_of_interest, stations)

        assert len(result) == 1
        assert result[0].lat == pytest.approx(49.5)
        assert result[0].lon == pytest.approx(-123.5)
        assert result[0].elevation == 750
        assert result[0].temperature == pytest.approx(22.5)
        assert result[0].relative_humidity == pytest.approx(50.0)
        assert result[0].precipitation == pytest.approx(0.0)
        assert result[0].wind_speed == pytest.approx(10.0)
