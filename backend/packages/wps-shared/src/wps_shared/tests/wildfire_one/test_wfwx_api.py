"""Unit tests for wfwx_api.py"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientSession
from wps_shared.db.models.forecasts import NoonForecast
from wps_shared.db.models.observations import HourlyActual
from wps_shared.schemas.fba import FireCentre
from wps_shared.schemas.morecast_v2 import StationDailyFromWF1
from wps_shared.schemas.stations import (
    GeoJsonDetailedWeatherStation,
    WeatherStation,
    WeatherVariables,
)
from wps_shared.wildfire_one.schema_parsers import (
    WFWXWeatherStation,
)
from wps_shared.wildfire_one.wfwx_api import (
    get_auth_header,
    get_dailies_for_stations_and_date,
    get_dailies_generator,
    get_daily_determinates_for_stations_and_date,
    get_detailed_geojson_stations,
    get_detailed_stations,
    get_fire_centers,
    get_forecasts_for_stations_by_date_range,
    get_hourly_actuals_all_stations,
    get_no_cache_auth_header,
    get_noon_forecasts_all_stations,
    get_raw_dailies_in_range_generator,
    get_station_data,
    get_station_groups,
    get_stations_by_codes,
    get_stations_by_group_ids,
    get_wfwx_stations_from_station_codes,
)


class MockAsyncGenerator:
    """Mock async generator for testing"""

    def __init__(self, items):
        self.items = items

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.items:
            return self.items.pop(0)
        else:
            raise StopAsyncIteration


class TestGetAuthHeader:
    """Test cases for the get_auth_header function"""

    @pytest.mark.anyio
    @patch("wps_shared.wildfire_one.wfwx_api.create_wps_wf1_client")
    @patch("wps_shared.wildfire_one.wfwx_api.config.get")
    async def test_get_auth_header(self, mock_config, mock_create_client):
        """Test get_auth_header returns correct auth header"""
        # Setup mocks
        mock_config.return_value = "600"
        mock_client = AsyncMock()
        mock_client.fetch_access_token.return_value = {"access_token": "test_token"}
        mock_create_client.return_value = mock_client

        session = MagicMock(spec=ClientSession)

        # Call function
        result = await get_auth_header(session)

        # Verify result
        assert result == {"Authorization": "Bearer test_token"}
        mock_client.fetch_access_token.assert_called_once_with(600)


class TestGetNoCacheAuthHeader:
    """Test cases for the get_no_cache_auth_header function"""

    @pytest.mark.anyio
    @patch("wps_shared.wildfire_one.wfwx_api.get_auth_header")
    async def test_get_no_cache_auth_header(self, mock_get_auth_header):
        """Test get_no_cache_auth_header adds no-cache header"""
        # Setup mocks
        mock_get_auth_header.return_value = {"Authorization": "Bearer test_token"}

        session = MagicMock(spec=ClientSession)

        # Call function
        result = await get_no_cache_auth_header(session)

        # Verify result
        assert result == {"Authorization": "Bearer test_token", "Cache-Control": "no-cache"}
        mock_get_auth_header.assert_called_once_with(session)


class TestGetStationsByCodes:
    """Test cases for the get_stations_by_codes function"""

    @pytest.mark.anyio
    @patch("wps_shared.wildfire_one.wfwx_api.EcodivisionSeasons")
    @patch("wps_shared.wildfire_one.wfwx_api.ClientSession")
    @patch("wps_shared.wildfire_one.wfwx_api.get_auth_header")
    @patch("wps_shared.wildfire_one.wfwx_api.create_wps_wf1_client")
    @patch("wps_shared.wildfire_one.wfwx_api.config.get")
    @patch("wps_shared.wildfire_one.wfwx_api.is_station_valid")
    @patch("wps_shared.wildfire_one.wfwx_api.parse_station")
    async def test_get_stations_by_codes_with_valid_stations(
        self,
        mock_parse_station,
        mock_is_station_valid,
        mock_config,
        mock_create_client,
        mock_get_auth_header,
        mock_client_session,
        mock_eco_division,
    ):
        """Test get_stations_by_codes returns stations when they are valid"""
        # Setup mocks
        mock_config.return_value = "604800"
        mock_get_auth_header.return_value = {"Authorization": "Bearer token"}

        mock_client = MagicMock()
        mock_client.fetch_paged_response_generator = MagicMock(
            return_value=MockAsyncGenerator(
                [
                    {"id": 1, "stationCode": 101, "displayLabel": "Station 1"},
                    {"id": 2, "stationCode": 102, "displayLabel": "Station 2"},
                    {"id": 3, "stationCode": 103, "displayLabel": "Station 3"},
                ]
            )
        )

        mock_create_client.return_value = mock_client
        # Station 103 should not be included in the results
        mock_is_station_valid.side_effect = lambda station: station.get("stationCode") != 103
        mock_parsed_station1 = MagicMock(spec=WeatherStation)
        mock_parsed_station2 = MagicMock(spec=WeatherStation)
        mock_parse_station.side_effect = [mock_parsed_station1, mock_parsed_station2]

        mock_eco_division_instance = MagicMock()
        mock_eco_division.return_value.__enter__.return_value = mock_eco_division_instance

        # Mock ClientSession context manager
        mock_session_instance = MagicMock()
        mock_client_session.return_value.__aenter__.return_value = mock_session_instance

        # Call function
        result = await get_stations_by_codes([101, 102, 103])

        # Verify result
        assert len(result) == 2
        assert result[0] == mock_parsed_station1
        assert result[1] == mock_parsed_station2

        # Verify calls
        mock_client_session.assert_called_once()
        mock_get_auth_header.assert_called_once_with(mock_session_instance)
        mock_create_client.assert_called_once_with(mock_session_instance)
        mock_client.fetch_paged_response_generator.assert_called_once()


class TestGetStationData:
    """Test cases for the get_station_data function"""

    @pytest.mark.anyio
    @patch("wps_shared.wildfire_one.wfwx_api.ClientSession")
    @patch("wps_shared.wildfire_one.wfwx_api.get_auth_header")
    @patch("wps_shared.wildfire_one.wfwx_api.create_wps_wf1_client")
    @patch("wps_shared.wildfire_one.wfwx_api.config.get")
    async def test_get_station_data(
        self, mock_config, mock_create_client, mock_get_auth_header, mock_client_session
    ):
        """Test get_station_data returns mapped stations"""
        # Setup mocks
        mock_config.return_value = "604800"
        mock_get_auth_header.return_value = {"Authorization": "Bearer token"}

        mock_client = MagicMock()
        mock_client.fetch_paged_response_generator = MagicMock(
            return_value=MockAsyncGenerator(
                [
                    {"id": 1, "stationCode": 101, "displayLabel": "Station 1"},
                    {"id": 2, "stationCode": 102, "displayLabel": "Station 2"},
                    {"id": 3, "stationCode": 103, "displayLabel": "Station 3"},
                ]
            )
        )
        mock_create_client.return_value = mock_client

        mock_mapper = AsyncMock(return_value=["mapped_station1", "mapped_station2"])

        # Mock ClientSession context manager
        mock_session_instance = MagicMock()
        mock_client_session.return_value.__aenter__.return_value = mock_session_instance

        # Call function
        result = await get_station_data(
            mock_session_instance, {"Authorization": "Bearer token"}, mapper=mock_mapper
        )

        # Verify result
        assert result == ["mapped_station1", "mapped_station2"]


class TestGetDetailedGeoJsonStations:
    """Test cases for the get_detailed_geojson_stations function"""

    @pytest.mark.anyio
    @patch("wps_shared.wildfire_one.wfwx_api.create_wps_wf1_client")
    @patch("wps_shared.wildfire_one.wfwx_api.config.get")
    @patch("wps_shared.wildfire_one.wfwx_api.is_station_valid")
    async def test_get_detailed_geojson_stations_with_valid_stations(
        self, mock_is_station_valid, mock_config, mock_create_client
    ):
        """Test get_detailed_geojson_stations returns correct mapping for valid stations"""
        # Setup mocks
        mock_config.return_value = "604800"
        mock_is_station_valid.return_value = True

        mock_client = MagicMock()
        mock_client.fetch_paged_response_generator = MagicMock(
            return_value=MockAsyncGenerator(
                [
                    {
                        "id": "station1",
                        "stationCode": 101,
                        "displayLabel": "Station 1",
                        "longitude": -123.45,
                        "latitude": 49.28,
                        "stationStatus": {"id": "ACTIVE"},
                    },
                    {
                        "id": "station2",
                        "stationCode": 102,
                        "displayLabel": "Station 2",
                        "longitude": -123.46,
                        "latitude": 49.29,
                        "stationStatus": {"id": "ACTIVE"},
                    },
                ]
            )
        )
        mock_create_client.return_value = mock_client

        session = MagicMock(spec=ClientSession)
        headers = {"Authorization": "Bearer token"}
        query_builder = MagicMock()

        # Call function
        stations, id_to_code_map = await get_detailed_geojson_stations(
            session, headers, query_builder
        )

        # Verify result
        assert len(stations) == 2
        assert 101 in stations
        assert 102 in stations
        assert stations[101].properties.code == 101
        assert stations[101].properties.name == "Station 1"
        assert stations[101].geometry.coordinates == [-123.45, 49.28]

        assert id_to_code_map == {"station1": 101, "station2": 102}


class TestGetDetailedStations:
    """Test cases for the get_detailed_stations function"""

    @pytest.mark.anyio
    @patch("wps_shared.wildfire_one.wfwx_api.get_auth_header")
    @patch("wps_shared.wildfire_one.wfwx_api._get_noon_date")
    @patch("wps_shared.wildfire_one.wfwx_api.create_wps_wf1_client")
    @patch("wps_shared.wildfire_one.wfwx_api.get_detailed_geojson_stations")
    @patch("wps_shared.wildfire_one.wfwx_api.ClientSession")
    @patch("wps_shared.wildfire_one.wfwx_api.TCPConnector")
    @patch("wps_shared.wildfire_one.wfwx_api.WeatherVariables")
    async def test_get_detailed_stations(
        self,
        mock_weather_variables,
        mock_tcp_connector,
        mock_client_session,
        mock_get_detailed_geojson_stations,
        mock_create_client,
        mock_get_noon_date,
        mock_get_auth_header,
    ):
        """Test get_detailed_stations returns stations with weather data"""
        # Setup mocks
        time_of_interest = datetime(2023, 1, 1, 12, 0, 0)
        noon_time = datetime(2023, 1, 1, 12, 0, 0)
        mock_get_noon_date.return_value = noon_time
        mock_get_auth_header.return_value = {"Authorization": "Bearer token"}

        mock_client = AsyncMock()
        mock_client.fetch_raw_dailies_for_all_stations.return_value = [
            {
                "stationId": "station1",
                "temperature": 20.5,
                "relativeHumidity": 65.0,
                "recordType": {"id": "ACTUAL"},
            }
        ]
        mock_create_client.return_value = mock_client

        # Mock geojson stations
        station1 = MagicMock(spec=GeoJsonDetailedWeatherStation)
        station1.properties = MagicMock()
        station1.properties.observations = None
        station1.properties.forecasts = None

        stations_dict = {101: station1}
        id_to_code_map = {"station1": 101}
        mock_get_detailed_geojson_stations.return_value = (stations_dict, id_to_code_map)

        mock_weather_variables.return_value = MagicMock(spec=WeatherVariables)

        # Mock TCPConnector
        mock_connector = MagicMock()
        mock_tcp_connector.return_value = mock_connector

        # Mock ClientSession context manager
        mock_session_instance = MagicMock()
        mock_client_session.return_value.__aenter__.return_value = mock_session_instance

        # Call function
        result = await get_detailed_stations(time_of_interest)

        # Verify result
        assert len(result) == 1
        assert result[0] == station1
        assert station1.properties.observations is not None


class TestGetNoonForecastsAllStations:
    """Test cases for the get_noon_forecasts_all_stations function"""

    @pytest.mark.anyio
    @patch("wps_shared.wildfire_one.wfwx_api.create_wps_wf1_client")
    @patch("wps_shared.wildfire_one.wfwx_api.get_station_data")
    @patch("wps_shared.wildfire_one.wfwx_api.parse_noon_forecast")
    async def test_get_noon_forecasts_all_stations(
        self, mock_parse_noon_forecast, mock_get_station_data, mock_create_client
    ):
        """Test get_noon_forecasts_all_stations returns forecasts for all stations"""
        # Setup mocks
        mock_client = MagicMock()
        mock_client.fetch_paged_response_generator = MagicMock(
            return_value=MockAsyncGenerator(
                [{"stationId": "wfwx1", "temp": 20.0}, {"stationId": "wfwx2", "temp": 22.0}]
            )
        )
        mock_create_client.return_value = mock_client

        mock_station1 = MagicMock(spec=WFWXWeatherStation)
        mock_station1.wfwx_id = "wfwx1"
        mock_station1.code = 101
        mock_station2 = MagicMock(spec=WFWXWeatherStation)
        mock_station2.wfwx_id = "wfwx2"
        mock_station2.code = 102
        mock_get_station_data.return_value = [mock_station1, mock_station2]

        mock_forecast1 = MagicMock(spec=NoonForecast)
        mock_forecast2 = MagicMock(spec=NoonForecast)
        mock_parse_noon_forecast.side_effect = [mock_forecast1, mock_forecast2]

        session = MagicMock(spec=ClientSession)
        header = {"Authorization": "Bearer token"}
        start_timestamp = datetime(2023, 1, 1, 0, 0, 0)

        # Call function
        result = await get_noon_forecasts_all_stations(session, header, start_timestamp)

        # Verify result
        assert len(result) == 2
        assert result[0] == mock_forecast1
        assert result[1] == mock_forecast2


class TestGetHourlyActualsAllStations:
    """Test cases for the get_hourly_actuals_all_stations function"""

    @pytest.mark.anyio
    @patch("wps_shared.wildfire_one.wfwx_api.create_wps_wf1_client")
    @patch("wps_shared.wildfire_one.wfwx_api.get_station_data")
    @patch("wps_shared.wildfire_one.wfwx_api.parse_hourly_actual")
    async def test_get_hourly_actuals_all_stations(
        self, mock_parse_hourly_actual, mock_get_station_data, mock_create_client
    ):
        """Test get_hourly_actuals_all_stations returns actuals for all stations"""
        # Setup mocks
        mock_client = MagicMock()
        mock_client.fetch_paged_response_generator = MagicMock(
            return_value=MockAsyncGenerator(
                [
                    {
                        "stationId": "wfwx1",
                        "hourlyMeasurementTypeCode": {"id": "ACTUAL"},
                        "temp": 20.0,
                    },
                    {
                        "stationId": "wfwx2",
                        "hourlyMeasurementTypeCode": {"id": "FORECAST"},  # Should be filtered out
                        "temp": 22.0,
                    },
                    {
                        "stationId": "wfwx1",
                        "hourlyMeasurementTypeCode": {"id": "ACTUAL"},
                        "temp": 21.0,
                    },
                ]
            )
        )
        mock_create_client.return_value = mock_client

        mock_station1 = MagicMock(spec=WFWXWeatherStation)
        mock_station1.wfwx_id = "wfwx1"
        mock_station1.code = 101
        mock_station2 = MagicMock(spec=WFWXWeatherStation)
        mock_station2.wfwx_id = "wfwx2"
        mock_station2.code = 102
        mock_get_station_data.return_value = [mock_station1, mock_station2]

        mock_actual1 = MagicMock(spec=HourlyActual)
        mock_actual2 = MagicMock(spec=HourlyActual)
        mock_parse_hourly_actual.side_effect = [mock_actual1, mock_actual2]

        session = MagicMock(spec=ClientSession)
        header = {"Authorization": "Bearer token"}
        start_timestamp = datetime(2023, 1, 1, 0, 0, 0)
        end_timestamp = datetime(2023, 1, 1, 23, 59, 59)

        # Call function
        result = await get_hourly_actuals_all_stations(
            session, header, start_timestamp, end_timestamp
        )

        # Verify result - should only include ACTUAL records (2 out of 3)
        assert len(result) == 2
        assert result[0] == mock_actual1
        assert result[1] == mock_actual2


class TestGetWfwxStationsFromStationCodes:
    """Test cases for the get_wfwx_stations_from_station_codes function"""

    @pytest.mark.anyio
    @patch("wps_shared.wildfire_one.wfwx_api.get_station_data")
    @patch("wps_shared.wildfire_one.wfwx_api.get_fire_centre_station_codes")
    async def test_get_wfwx_stations_from_station_codes_with_specific_codes(
        self, mock_get_fire_centre_station_codes, mock_get_station_data
    ):
        """Test get_wfwx_stations_from_station_codes returns specific stations when codes provided"""
        # Setup mocks
        mock_get_fire_centre_station_codes.return_value = [101, 102, 103, 104]

        mock_station1 = MagicMock(spec=WFWXWeatherStation)
        mock_station1.code = 101
        mock_station1.wfwx_id = "wfwx1"
        mock_station2 = MagicMock(spec=WFWXWeatherStation)
        mock_station2.code = 102
        mock_station2.wfwx_id = "wfwx2"
        mock_station3 = MagicMock(spec=WFWXWeatherStation)
        mock_station3.code = 103
        mock_station3.wfwx_id = "wfwx3"
        mock_get_station_data.return_value = [mock_station1, mock_station2, mock_station3]

        session = MagicMock(spec=ClientSession)
        header = {"Authorization": "Bearer token"}
        station_codes = [101, 102]

        # Call function
        result = await get_wfwx_stations_from_station_codes(session, header, station_codes)

        # Verify result
        assert len(result) == 2
        assert result[0] == mock_station1
        assert result[1] == mock_station2

    @pytest.mark.anyio
    @patch("wps_shared.wildfire_one.wfwx_api.get_station_data")
    @patch("wps_shared.wildfire_one.wfwx_api.get_fire_centre_station_codes")
    async def test_get_wfwx_stations_from_station_codes_none_returns_all(
        self, mock_get_fire_centre_station_codes, mock_get_station_data
    ):
        """Test get_wfwx_stations_from_station_codes returns all fire centre stations when None provided"""
        # Setup mocks
        mock_get_fire_centre_station_codes.return_value = [
            101,
            102,
        ]  # Only station 101, 102 are in fire centre

        mock_station1 = MagicMock(spec=WFWXWeatherStation)
        mock_station1.code = 101
        mock_station1.wfwx_id = "wfwx1"
        mock_station2 = MagicMock(spec=WFWXWeatherStation)
        mock_station2.code = 102
        mock_station2.wfwx_id = "wfwx2"
        mock_station3 = MagicMock(spec=WFWXWeatherStation)
        mock_station3.code = 103  # Not in fire centre
        mock_station3.wfwx_id = "wfwx3"
        mock_get_station_data.return_value = [mock_station1, mock_station2, mock_station3]

        session = MagicMock(spec=ClientSession)
        header = {"Authorization": "Bearer token"}
        station_codes = None

        # Call function
        result = await get_wfwx_stations_from_station_codes(session, header, station_codes)

        # Verify result - should only include fire centre stations
        assert len(result) == 2
        assert result[0] == mock_station1
        assert result[1] == mock_station2


class TestGetRawDailiesInRangeGenerator:
    """Test cases for the get_raw_dailies_in_range_generator function"""

    @pytest.mark.anyio
    @patch("wps_shared.wildfire_one.wfwx_api.create_wps_wf1_client")
    async def test_get_raw_dailies_in_range_generator(self, mock_create_client):
        """Test get_raw_dailies_in_range_generator returns correct generator"""
        # Setup mocks
        mock_client = MagicMock()
        mock_client.fetch_paged_response_generator = MagicMock(
            return_value=MockAsyncGenerator(
                [{"id": "daily1", "temp": 20.0}, {"id": "daily2", "temp": 22.0}]
            )
        )
        mock_create_client.return_value = mock_client

        session = MagicMock(spec=ClientSession)
        header = {"Authorization": "Bearer token"}
        wfwx_station_ids = ["wfwx1", "wfwx2"]
        start_timestamp = 1672531200000  # 2023-01-01 00:00:00 in milliseconds
        end_timestamp = 1672617600000  # 2023-01-02 00:00:00 in milliseconds

        # Call function
        result = await get_raw_dailies_in_range_generator(
            session, header, wfwx_station_ids, start_timestamp, end_timestamp
        )

        # Verify result is the generator
        assert isinstance(result, MockAsyncGenerator)

        # Verify client was called correctly
        mock_create_client.assert_called_once_with(session)


class TestGetDailiesGenerator:
    """Test cases for the get_dailies_generator function"""

    @pytest.mark.anyio
    @patch("wps_shared.wildfire_one.wfwx_api.create_wps_wf1_client")
    @patch("wps_shared.wildfire_one.wfwx_api.config.get")
    async def test_get_dailies_generator_with_cache(self, mock_config, mock_create_client):
        """Test get_dailies_generator uses cache when enabled"""
        mock_mapping = {"REDIS_DAILIES_BY_STATION_CODE_CACHE_EXPIRY": "300", "REDIS_USE": "True"}

        # Setup mocks
        def mock_config_get(key, default=None):
            return mock_mapping.get(key, default)

        mock_config.side_effect = mock_config_get

        mock_client = MagicMock()
        mock_client.fetch_paged_response_generator = MagicMock(
            return_value=MockAsyncGenerator([{"id": "daily1", "temp": 20.0}])
        )
        mock_create_client.return_value = mock_client

        mock_station = MagicMock(spec=WFWXWeatherStation)
        mock_station.wfwx_id = "wfwx1"

        session = MagicMock(spec=ClientSession)
        header = {"Authorization": "Bearer token"}
        wfwx_stations = [mock_station]
        time_of_interest = datetime(2023, 1, 1, 12, 0, 0)
        end_time_of_interest = datetime(2023, 1, 2, 12, 0, 0)
        check_cache = True

        # Call function
        result = await get_dailies_generator(
            session, header, wfwx_stations, time_of_interest, end_time_of_interest, check_cache
        )

        # Verify result
        assert isinstance(result, MockAsyncGenerator)

        # Verify cache was used
        mock_client.fetch_paged_response_generator.assert_called_once()


class TestGetFireCenters:
    """Test cases for the get_fire_centers function"""

    @pytest.mark.anyio
    @patch("wps_shared.wildfire_one.wfwx_api.get_station_data")
    async def test_get_fire_centers(self, mock_get_station_data):
        """Test get_fire_centers returns list of fire centres"""
        # Setup mocks
        mock_fire_center1 = MagicMock(spec=FireCentre)
        mock_fire_center2 = MagicMock(spec=FireCentre)
        fire_centers_dict = {"center1": mock_fire_center1, "center2": mock_fire_center2}
        mock_get_station_data.return_value = fire_centers_dict

        session = MagicMock(spec=ClientSession)
        header = {"Authorization": "Bearer token"}

        # Call function
        result = await get_fire_centers(session, header)

        # Verify result
        assert len(result) == 2
        assert mock_fire_center1 in result
        assert mock_fire_center2 in result


class TestGetDailiesForStationsAndDate:
    """Test cases for the get_dailies_for_stations_and_date function"""

    @pytest.mark.anyio
    @patch("wps_shared.wildfire_one.wfwx_api.is_station_valid")
    @patch("wps_shared.wildfire_one.wfwx_api.get_wfwx_stations_from_station_codes")
    @patch("wps_shared.wildfire_one.wfwx_api.get_dailies_generator")
    async def test_get_dailies_for_stations_and_date(
        self, mock_get_dailies_generator, mock_get_wfwx_stations, mock_is_station_valid
    ):
        """Test get_dailies_for_stations_and_date returns mapped dailies"""
        # Setup mocks
        mock_wfwx_station = MagicMock(spec=WFWXWeatherStation)
        mock_wfwx_station.wfwx_id = "wfwx1"
        mock_get_wfwx_stations.return_value = [mock_wfwx_station]
        mock_is_station_valid.return_value = True
        mock_dailies_list_mapper_result = ["mapped_daily1", "mapped_daily2"]
        mock_dailies_list_mapper = AsyncMock(return_value=mock_dailies_list_mapper_result)

        # Need to access and modify the __defaults__ of the function being called (get_dailies_for_stations_and_date)
        original_defaults = get_dailies_for_stations_and_date.__defaults__
        try:
            new_defaults = list(original_defaults or [])
            if len(new_defaults) == 0:
                # If there were no defaults, we must build a defaults tuple that
                # matches number of rightmost defaulted params.
                new_defaults = [mock_dailies_list_mapper]
            else:
                # Replace the last default (mapper)
                new_defaults[-1] = mock_dailies_list_mapper
            get_dailies_for_stations_and_date.__defaults__ = tuple(new_defaults)

            mock_dailies_generator = MockAsyncGenerator(
                [{"id": "daily1", "temp": 20.0}, {"id": "daily2", "temp": 22.0}]
            )
            mock_get_dailies_generator.return_value = mock_dailies_generator

            session = MagicMock(spec=ClientSession)
            header = {"Authorization": "Bearer token"}
            start_time_of_interest = datetime(2023, 1, 1, 12, 0, 0)
            end_time_of_interest = datetime(2023, 1, 2, 12, 0, 0)
            unique_station_codes = [101, 102]

            # Call function
            result = await get_dailies_for_stations_and_date(
                session, header, start_time_of_interest, end_time_of_interest, unique_station_codes
            )

            # Verify result
            assert result == mock_dailies_list_mapper_result
            assert mock_dailies_list_mapper.await_count == 1
        finally:
            # Always restore defaults to avoid test bleed-over
            get_dailies_for_stations_and_date.__defaults__ = original_defaults


class TestGetForecastsForStationsByDateRange:
    """Test cases for the get_forecasts_for_stations_by_date_range function"""

    @pytest.mark.anyio
    @patch("wps_shared.wildfire_one.wfwx_api.is_station_valid")
    @patch("wps_shared.wildfire_one.wfwx_api.get_wfwx_stations_from_station_codes")
    @patch("wps_shared.wildfire_one.wfwx_api.get_dailies_generator")
    async def test_get_forecasts_for_stations_by_date_range(
        self, mock_get_dailies_generator, mock_get_wfwx_stations, mock_is_station_valid
    ):
        """Test get_forecasts_for_stations_by_date_range returns forecast dailies"""
        # Setup mocks
        mock_wfwx_station = MagicMock(spec=WFWXWeatherStation)
        mock_wfwx_station.wfwx_id = "wfwx1"
        mock_get_wfwx_stations.return_value = [mock_wfwx_station]
        mock_is_station_valid.return_value = True

        mock_dailies_generator = MockAsyncGenerator(
            [{"id": "forecast1", "temp": 20.0}, {"id": "forecast2", "temp": 22.0}]
        )
        mock_get_dailies_generator.return_value = mock_dailies_generator
        mock_dailies_list_mapper_result = [
            MagicMock(spec=StationDailyFromWF1),
            MagicMock(spec=StationDailyFromWF1),
        ]
        mock_dailies_list_mapper = AsyncMock(return_value=mock_dailies_list_mapper_result)

        # Need to access and modify the __defaults__ of the function being called (get_dailies_for_stations_and_date)
        original_defaults = get_forecasts_for_stations_by_date_range.__defaults__
        try:
            new_defaults = list(original_defaults or [])
            if len(new_defaults) == 0:
                # If there were no defaults, we must build a defaults tuple that
                # matches number of rightmost defaulted params.
                new_defaults = [mock_dailies_list_mapper]
            else:
                # Replace the last default (mapper)
                new_defaults[-1] = mock_dailies_list_mapper
            get_forecasts_for_stations_by_date_range.__defaults__ = tuple(new_defaults)

            session = MagicMock(spec=ClientSession)
            header = {"Authorization": "Bearer token"}
            start_time_of_interest = datetime(2023, 1, 1, 12, 0, 0)
            end_time_of_interest = datetime(2023, 1, 2, 12, 0, 0)
            unique_station_codes = [101, 102]

            # Call function
            result = await get_forecasts_for_stations_by_date_range(
                session, header, start_time_of_interest, end_time_of_interest, unique_station_codes
            )

            # Verify result
            assert result == mock_dailies_list_mapper_result
            assert mock_dailies_list_mapper.await_count == 1
        finally:
            # Always restore defaults to avoid test bleed-over
            get_forecasts_for_stations_by_date_range.__defaults__ = original_defaults


class TestGetDailyDeterminatesForStationsAndDate:
    """Test cases for the get_daily_determinates_for_stations_and_date function"""

    @pytest.mark.anyio
    @patch("wps_shared.wildfire_one.wfwx_api.get_wfwx_stations_from_station_codes")
    @patch("wps_shared.wildfire_one.wfwx_api.get_dailies_generator")
    async def test_get_daily_determinates_for_stations_and_date(
        self, mock_get_dailies_generator, mock_get_wfwx_stations
    ):
        """Test get_daily_determinates_for_stations_and_date returns actuals and forecasts"""
        # Setup mocks
        mock_wfwx_station = MagicMock(spec=WFWXWeatherStation)
        mock_wfwx_station.wfwx_id = "wfwx1"
        mock_get_wfwx_stations.return_value = [mock_wfwx_station]

        mock_dailies_generator = MockAsyncGenerator(
            [{"id": "daily1", "temp": 20.0}, {"id": "daily2", "temp": 22.0}]
        )
        mock_get_dailies_generator.return_value = mock_dailies_generator

        mock_actuals = ["actual1", "actual2"]
        mock_forecasts = ["forecast1", "forecast2"]
        mock_weather_indeterminate_list_mapper = AsyncMock(
            return_value=(mock_actuals, mock_forecasts)
        )

        # Need to access and modify the __defaults__ of the function being called (get_dailies_for_stations_and_date)
        original_defaults = get_daily_determinates_for_stations_and_date.__defaults__
        try:
            new_defaults = list(original_defaults or [])
            if len(new_defaults) == 0:
                # If there were no defaults, we must build a defaults tuple that
                # matches number of rightmost defaulted params.
                new_defaults = [mock_weather_indeterminate_list_mapper]
            else:
                # Replace the first default (mapper)
                new_defaults[0] = mock_weather_indeterminate_list_mapper
            get_daily_determinates_for_stations_and_date.__defaults__ = tuple(new_defaults)

            session = MagicMock(spec=ClientSession)
            header = {"Authorization": "Bearer token"}
            start_time_of_interest = datetime(2023, 1, 1, 12, 0, 0)
            end_time_of_interest = datetime(2023, 1, 2, 12, 0, 0)
            unique_station_codes = [101, 102]

            # Call function
            result = await get_daily_determinates_for_stations_and_date(
                session, header, start_time_of_interest, end_time_of_interest, unique_station_codes
            )

            # Verify result
            assert result == (mock_actuals, mock_forecasts)
            assert mock_weather_indeterminate_list_mapper.await_count == 1
        finally:
            # Always restore defaults to avoid test bleed-over
            get_daily_determinates_for_stations_and_date.__defaults__ = original_defaults


class TestGetStationGroups:
    """Test cases for the get_station_groups function"""

    @pytest.mark.anyio
    @patch("wps_shared.wildfire_one.wfwx_api.ClientSession")
    @patch("wps_shared.wildfire_one.wfwx_api.get_auth_header")
    @patch("wps_shared.wildfire_one.wfwx_api.create_wps_wf1_client")
    async def test_get_station_groups(
        self, mock_create_client, mock_get_auth_header, mock_client_session
    ):
        """Test get_station_groups returns mapped station groups"""
        # Setup mocks
        mock_get_auth_header.return_value = {"Authorization": "Bearer token"}

        mock_client = AsyncMock()
        mock_client.fetch_paged_response_generator.return_value = MockAsyncGenerator(
            [{"id": "group1", "name": "Group 1"}, {"id": "group2", "name": "Group 2"}]
        )
        mock_create_client.return_value = mock_client

        mock_weather_station_group_mapper_value = ["mapped_group1", "mapped_group2"]
        mock_weather_station_group_mapper = AsyncMock(
            return_value=mock_weather_station_group_mapper_value
        )

        # Need to access and modify the __defaults__ of the function being called (get_dailies_for_stations_and_date)
        original_defaults = get_station_groups.__defaults__
        try:
            new_defaults = list(original_defaults or [])
            if len(new_defaults) == 0:
                # If there were no defaults, we must build a defaults tuple that
                # matches number of rightmost defaulted params.
                new_defaults = [mock_weather_station_group_mapper]
            else:
                # Replace the last (only) default (mapper)
                new_defaults[-1] = mock_weather_station_group_mapper
            get_station_groups.__defaults__ = tuple(new_defaults)

            # Mock ClientSession context manager
            mock_session_instance = MagicMock()
            mock_client_session.return_value.__aenter__.return_value = mock_session_instance

            # Call function
            result = await get_station_groups()

            # Verify result
            assert result == mock_weather_station_group_mapper_value
        finally:
            # Always restore defaults to avoid test bleed-over
            get_station_groups.__defaults__ = original_defaults


class TestGetStationsByGroupIds:
    """Test cases for the get_stations_by_group_ids function"""

    @pytest.mark.anyio
    @patch("wps_shared.wildfire_one.wfwx_api.ClientSession")
    @patch("wps_shared.wildfire_one.wfwx_api.get_auth_header")
    @patch("wps_shared.wildfire_one.wfwx_api.create_wps_wf1_client")
    async def test_get_stations_by_group_ids(
        self, mock_create_client, mock_get_auth_header, mock_client_session
    ):
        """Test get_stations_by_group_ids returns stations from all groups"""
        # Setup mocks
        mock_get_auth_header.return_value = {"Authorization": "Bearer token"}

        mock_client = AsyncMock()
        mock_client.fetch_stations_by_group_id.side_effect = [
            {"_embedded": {"stations": [{"id": "station1"}]}},
            {"_embedded": {"stations": [{"id": "station2"}]}},
        ]
        mock_create_client.return_value = mock_client

        # Mock ClientSession context manager
        mock_session_instance = MagicMock()
        mock_client_session.return_value.__aenter__.return_value = mock_session_instance

        # Call function
        group_ids = ["group1"]

        mock_mapped_stations_group1 = "mapped_station1"
        mock_mapped_stations_group2 = "mapped_station2"
        mock_unique_weather_stations_mapper_value = [
            mock_mapped_stations_group1,
            mock_mapped_stations_group2,
        ]
        mock_unique_weather_stations_mapper = MagicMock(
            return_value=mock_unique_weather_stations_mapper_value
        )

        # Need to access and modify the __defaults__ of the function being called (get_dailies_for_stations_and_date)
        original_defaults = get_stations_by_group_ids.__defaults__
        try:
            new_defaults = list(original_defaults or [])
            if len(new_defaults) == 0:
                # If there were no defaults, we must build a defaults tuple that
                # matches number of rightmost defaulted params.
                new_defaults = [mock_unique_weather_stations_mapper]
            else:
                # Replace the last (only) default (mapper)
                new_defaults[-1] = mock_unique_weather_stations_mapper
            get_stations_by_group_ids.__defaults__ = tuple(new_defaults)

            result = await get_stations_by_group_ids(group_ids)

            # Verify result
            assert result == ["mapped_station1", "mapped_station2"]
            assert mock_client.fetch_stations_by_group_id.call_count == 1
            assert mock_unique_weather_stations_mapper.call_count == 1
        finally:
            # Always restore defaults to avoid test bleed-over
            get_stations_by_group_ids.__defaults__ = original_defaults
