"""
Unit tests for temperature interpolation module.
"""

import pytest
import numpy as np
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from wps_shared.schemas.sfms import StationTemperature
from wps_shared.schemas.stations import WeatherStation
from wps_shared.geospatial.spatial_interpolation import (
    haversine_distance,
    idw_interpolation,
)
from wps_shared.sfms.raster_addresser import RasterKeyAddresser, WeatherParameter
from app.sfms.temperature_interpolation import (
    adjust_temperature_to_sea_level,
    adjust_temperature_to_elevation,
    DRY_ADIABATIC_LAPSE_RATE,
    fetch_station_temperatures,
    interpolate_temperature_to_raster,
    get_dem_path,
)


class TestStationTemperature:
    """Tests for StationTemperature class."""

    def test_station_temperature_initialization(self):
        """Test that StationTemperature initializes correctly."""
        station = StationTemperature(
            code=123, lat=49.0, lon=-123.0, elevation=500.0, temperature=20.0
        )
        assert station.code == 123
        assert station.lat == 49.0
        assert station.lon == -123.0
        assert station.elevation == 500.0
        assert station.temperature == 20.0
        assert station.sea_level_temp is None


class TestElevationAdjustment:
    """Tests for temperature elevation adjustment functions."""

    def test_adjust_to_sea_level(self):
        """Test adjusting temperature to sea level."""
        station = StationTemperature(
            code=123,
            lat=49.0,
            lon=-123.0,
            elevation=1000.0,  # 1000m elevation
            temperature=10.0,  # 10°C at 1000m
        )

        # At 1000m elevation with lapse rate 0.0098°C/m
        # Sea level temp = 10 + (1000 * 0.0098) = 10 + 9.8 = 19.8°C
        sea_level_temp = adjust_temperature_to_sea_level(station)

        assert sea_level_temp == pytest.approx(19.8, rel=1e-6)
        assert station.sea_level_temp == pytest.approx(19.8, rel=1e-6)

    def test_adjust_to_sea_level_zero_elevation(self):
        """Test that zero elevation doesn't change temperature."""
        station = StationTemperature(
            code=123, lat=49.0, lon=-123.0, elevation=0.0, temperature=15.0
        )

        sea_level_temp = adjust_temperature_to_sea_level(station)
        assert sea_level_temp == 15.0

    def test_adjust_from_sea_level_to_elevation(self):
        """Test adjusting from sea level to elevation."""
        sea_level_temp = 20.0
        elevation = 1000.0

        # At 1000m: temp = 20 - (1000 * 0.0098) = 20 - 9.8 = 10.2°C
        adjusted_temp = adjust_temperature_to_elevation(sea_level_temp, elevation)

        assert adjusted_temp == pytest.approx(10.2, rel=1e-6)

    def test_round_trip_elevation_adjustment(self):
        """Test that adjusting to sea level and back gives original temp."""
        original_temp = 15.0
        elevation = 500.0

        station = StationTemperature(
            code=123, lat=49.0, lon=-123.0, elevation=elevation, temperature=original_temp
        )

        sea_level_temp = adjust_temperature_to_sea_level(station)
        back_to_elevation = adjust_temperature_to_elevation(sea_level_temp, elevation)

        assert back_to_elevation == pytest.approx(original_temp, rel=1e-6)

    def test_lapse_rate_constant(self):
        """Verify the dry adiabatic lapse rate value."""
        # Standard dry adiabatic lapse rate is 9.8°C per 1000m
        assert DRY_ADIABATIC_LAPSE_RATE == pytest.approx(0.0098, rel=1e-6)


class TestHaversineDistance:
    """Tests for haversine distance calculation."""

    def test_same_point(self):
        """Test that distance between same point is zero."""
        lat, lon = 49.0, -123.0
        distance = haversine_distance(lat, lon, lat, lon)
        assert distance == pytest.approx(0.0, abs=1.0)  # Within 1 meter

    def test_known_distance(self):
        """Test haversine with known distance."""
        # Vancouver: 49.2827° N, 123.1207° W
        # Seattle: 47.6062° N, 122.3321° W
        # Approximate distance: ~195 km

        vancouver_lat, vancouver_lon = 49.2827, -123.1207
        seattle_lat, seattle_lon = 47.6062, -122.3321

        distance = haversine_distance(vancouver_lat, vancouver_lon, seattle_lat, seattle_lon)

        # Should be approximately 195 km (195000 meters)
        # Allow 5% tolerance
        assert distance == pytest.approx(195000, rel=0.05)

    def test_equator_distance(self):
        """Test distance along equator."""
        # 1 degree of longitude at equator ≈ 111.32 km
        distance = haversine_distance(0.0, 0.0, 0.0, 1.0)
        assert distance == pytest.approx(111320, rel=0.01)


class TestIDWInterpolation:
    """Tests for Inverse Distance Weighting interpolation."""

    def test_idw_exact_match(self):
        """Test that IDW returns station value when point is at station."""
        stations = [
            StationTemperature(code=1, lat=49.0, lon=-123.0, elevation=100, temperature=15.0),
            StationTemperature(code=2, lat=50.0, lon=-124.0, elevation=200, temperature=20.0),
        ]

        # Adjust to sea level
        for station in stations:
            adjust_temperature_to_sea_level(station)

        # Prepare lists for IDW
        lats = [s.lat for s in stations]
        lons = [s.lon for s in stations]
        values = [s.sea_level_temp for s in stations]

        # Query at exact station location
        result = idw_interpolation(49.0, -123.0, lats, lons, values)

        # Should return the sea level temp of the first station
        assert result == pytest.approx(stations[0].sea_level_temp, rel=1e-6)

    def test_idw_between_two_stations(self):
        """Test IDW interpolation between two stations."""
        stations = [
            StationTemperature(code=1, lat=49.0, lon=-123.0, elevation=0, temperature=10.0),
            StationTemperature(code=2, lat=50.0, lon=-123.0, elevation=0, temperature=20.0),
        ]

        # Adjust to sea level (no change since elevation is 0)
        for station in stations:
            adjust_temperature_to_sea_level(station)

        # Prepare lists for IDW
        lats = [s.lat for s in stations]
        lons = [s.lon for s in stations]
        values = [s.sea_level_temp for s in stations]

        # Query at midpoint
        result = idw_interpolation(49.5, -123.0, lats, lons, values)

        # Should be weighted average, closer to midpoint
        assert result is not None
        assert 10.0 < result < 20.0

    def test_idw_no_stations(self):
        """Test that IDW returns None when no stations provided."""
        result = idw_interpolation(49.0, -123.0, [], [], [])
        assert result is None

    def test_idw_outside_search_radius(self):
        """Test that IDW returns None when all stations outside search radius."""
        stations = [
            StationTemperature(code=1, lat=49.0, lon=-123.0, elevation=0, temperature=15.0),
        ]

        for station in stations:
            adjust_temperature_to_sea_level(station)

        # Prepare lists for IDW
        lats = [s.lat for s in stations]
        lons = [s.lon for s in stations]
        values = [s.sea_level_temp for s in stations]

        # Query far away (at least 200km away)
        result = idw_interpolation(52.0, -128.0, lats, lons, values, search_radius=100000)
        assert result is None

    def test_idw_with_none_sea_level_temp(self):
        """Test that IDW handles points with None values."""
        stations = [
            StationTemperature(code=1, lat=49.0, lon=-123.0, elevation=0, temperature=15.0),
            StationTemperature(code=2, lat=50.0, lon=-124.0, elevation=0, temperature=20.0),
        ]

        # Only adjust first station
        adjust_temperature_to_sea_level(stations[0])
        # Leave second station's sea_level_temp as None

        # Prepare lists for IDW (including None value)
        lats = [s.lat for s in stations]
        lons = [s.lon for s in stations]
        values = [stations[0].sea_level_temp, None]

        result = idw_interpolation(49.5, -123.5, lats, lons, values)

        # Should still work with only one valid station
        assert result is not None
        assert result == pytest.approx(stations[0].sea_level_temp, abs=1.0)


class TestS3KeyGeneration:
    """Tests for S3 key generation."""

    def test_interpolated_key_temp_format(self):
        """Test that interpolated temperature key has correct format."""
        addresser = RasterKeyAddresser()
        dt = datetime(2024, 1, 15, 20, 0, 0, tzinfo=timezone.utc)
        key = addresser.get_interpolated_key(dt, WeatherParameter.TEMP)

        expected = "sfms/interpolated/temp/2024/01/15/temp_20240115.tif"
        assert key == expected

    def test_interpolated_key_different_dates(self):
        """Test key generation for different dates."""
        addresser = RasterKeyAddresser()

        # Test December (month 12)
        dt = datetime(2024, 12, 31, 20, 0, 0, tzinfo=timezone.utc)
        key = addresser.get_interpolated_key(dt, WeatherParameter.TEMP)
        assert key == "sfms/interpolated/temp/2024/12/31/temp_20241231.tif"

        # Test single digit month
        dt = datetime(2024, 3, 5, 20, 0, 0, tzinfo=timezone.utc)
        key = addresser.get_interpolated_key(dt, WeatherParameter.TEMP)
        assert key == "sfms/interpolated/temp/2024/03/05/temp_20240305.tif"

    def test_interpolated_key_different_params(self):
        """Test key generation for different weather parameters."""
        addresser = RasterKeyAddresser()
        dt = datetime(2024, 1, 15, 20, 0, 0, tzinfo=timezone.utc)

        # Test RH
        rh_key = addresser.get_interpolated_key(dt, WeatherParameter.RH)
        assert rh_key == "sfms/interpolated/rh/2024/01/15/rh_20240115.tif"

        # Test Wind Speed
        wind_key = addresser.get_interpolated_key(dt, WeatherParameter.WIND_SPEED)
        assert wind_key == "sfms/interpolated/wind_speed/2024/01/15/wind_speed_20240115.tif"


class TestFetchStationTemperatures:
    """Tests for fetch_station_temperatures function."""

    @pytest.mark.anyio
    async def test_fetch_basic_success(self):
        """Test successful fetch of station temperatures."""
        # Setup mock session and headers
        mock_session = AsyncMock()
        headers = {"Authorization": "Bearer test_token"}
        time_of_interest = datetime(2024, 1, 15, 20, 0, 0, tzinfo=timezone.utc)

        # Create test stations
        stations = [
            WeatherStation(
                code=123,
                name="Test Station 1",
                lat=49.0,
                long=-123.0,
                elevation=500.0,
            ),
            WeatherStation(
                code=456,
                name="Test Station 2",
                lat=50.0,
                long=-124.0,
                elevation=1000.0,
            ),
        ]

        # Mock raw daily data from WF1
        raw_dailies = [
            {
                "stationData": {
                    "stationCode": 123,
                    "displayLabel": "Test Station 1",
                    "stationStatus": {"id": "ACTIVE"},
                    "latitude": 49.0,
                    "longitude": -123.0,
                },
                "temperature": 15.0,
                "recordType": {"id": "ACTUAL"},
            },
            {
                "stationData": {
                    "stationCode": 456,
                    "displayLabel": "Test Station 2",
                    "stationStatus": {"id": "ACTIVE"},
                    "latitude": 50.0,
                    "longitude": -124.0,
                },
                "temperature": 10.0,
                "recordType": {"id": "ACTUAL"},
            },
        ]

        # Mock the fetch_raw_dailies_for_all_stations function
        with patch(
            "app.sfms.temperature_interpolation.fetch_raw_dailies_for_all_stations",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = raw_dailies

            # Call the function
            result = await fetch_station_temperatures(
                mock_session, headers, time_of_interest, stations
            )

            # Verify results
            assert len(result) == 2
            assert result[0].code == 123
            assert result[0].temperature == 15.0
            assert result[0].elevation == 500.0
            assert result[1].code == 456
            assert result[1].temperature == 10.0
            assert result[1].elevation == 1000.0

    @pytest.mark.anyio
    async def test_fetch_filters_non_actual_records(self):
        """Test that non-ACTUAL records are filtered out."""
        mock_session = AsyncMock()
        headers = {"Authorization": "Bearer test_token"}
        time_of_interest = datetime(2024, 1, 15, 20, 0, 0, tzinfo=timezone.utc)

        stations = [
            WeatherStation(
                code=123, name="Test Station", lat=49.0, long=-123.0, elevation=500.0
            ),
        ]

        # Mock data with FORECAST record type (should be filtered)
        raw_dailies = [
            {
                "stationData": {
                    "stationCode": 123,
                    "displayLabel": "Test Station",
                    "stationStatus": {"id": "ACTIVE"},
                    "latitude": 49.0,
                    "longitude": -123.0,
                },
                "temperature": 15.0,
                "recordType": {"id": "FORECAST"},  # Not ACTUAL, should be skipped
            },
        ]

        with patch(
            "app.sfms.temperature_interpolation.fetch_raw_dailies_for_all_stations",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = raw_dailies

            result = await fetch_station_temperatures(
                mock_session, headers, time_of_interest, stations
            )

            # Should be empty since FORECAST records are filtered (line 68)
            assert len(result) == 0

    @pytest.mark.anyio
    async def test_fetch_handles_missing_temperature(self):
        """Test that stations with missing temperature are skipped."""
        mock_session = AsyncMock()
        headers = {"Authorization": "Bearer test_token"}
        time_of_interest = datetime(2024, 1, 15, 20, 0, 0, tzinfo=timezone.utc)

        stations = [
            WeatherStation(
                code=123, name="Test Station", lat=49.0, long=-123.0, elevation=500.0
            ),
        ]

        # Mock data with None temperature (should be skipped)
        raw_dailies = [
            {
                "stationData": {
                    "stationCode": 123,
                    "displayLabel": "Test Station",
                    "stationStatus": {"id": "ACTIVE"},
                    "latitude": 49.0,
                    "longitude": -123.0,
                },
                "temperature": None,  # Missing temperature, should be skipped
                "recordType": {"id": "ACTUAL"},
            },
        ]

        with patch(
            "app.sfms.temperature_interpolation.fetch_raw_dailies_for_all_stations",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = raw_dailies

            result = await fetch_station_temperatures(
                mock_session, headers, time_of_interest, stations
            )

            # Should be empty (lines 79-80)
            assert len(result) == 0

    @pytest.mark.anyio
    async def test_fetch_handles_missing_elevation(self):
        """Test that stations with missing elevation are skipped."""
        mock_session = AsyncMock()
        headers = {"Authorization": "Bearer test_token"}
        time_of_interest = datetime(2024, 1, 15, 20, 0, 0, tzinfo=timezone.utc)

        stations = [
            WeatherStation(
                code=123, name="Test Station", lat=49.0, long=-123.0, elevation=None
            ),
        ]

        raw_dailies = [
            {
                "stationData": {
                    "stationCode": 123,
                    "displayLabel": "Test Station",
                    "stationStatus": {"id": "ACTIVE"},
                    "latitude": 49.0,
                    "longitude": -123.0,
                },
                "temperature": 15.0,
                "recordType": {"id": "ACTUAL"},
            },
        ]

        with patch(
            "app.sfms.temperature_interpolation.fetch_raw_dailies_for_all_stations",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = raw_dailies

            result = await fetch_station_temperatures(
                mock_session, headers, time_of_interest, stations
            )

            # Should be empty due to missing elevation (lines 83-84)
            assert len(result) == 0

    @pytest.mark.anyio
    async def test_fetch_handles_unknown_station(self):
        """Test that stations not in lookup are skipped."""
        mock_session = AsyncMock()
        headers = {"Authorization": "Bearer test_token"}
        time_of_interest = datetime(2024, 1, 15, 20, 0, 0, tzinfo=timezone.utc)

        stations = [
            WeatherStation(
                code=123, name="Test Station", lat=49.0, long=-123.0, elevation=500.0
            ),
        ]

        # Raw daily for station 999 which is not in our station list
        raw_dailies = [
            {
                "stationData": {
                    "stationCode": 999,  # Not in station_lookup
                    "displayLabel": "Unknown Station",
                    "stationStatus": {"id": "ACTIVE"},
                    "latitude": 49.0,
                    "longitude": -123.0,
                },
                "temperature": 15.0,
                "recordType": {"id": "ACTUAL"},
            },
        ]

        with patch(
            "app.sfms.temperature_interpolation.fetch_raw_dailies_for_all_stations",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = raw_dailies

            result = await fetch_station_temperatures(
                mock_session, headers, time_of_interest, stations
            )

            # Should be empty (lines 72-73)
            assert len(result) == 0

    @pytest.mark.anyio
    async def test_fetch_handles_invalid_station_data(self):
        """Test that invalid station data is skipped."""
        mock_session = AsyncMock()
        headers = {"Authorization": "Bearer test_token"}
        time_of_interest = datetime(2024, 1, 15, 20, 0, 0, tzinfo=timezone.utc)

        stations = [
            WeatherStation(
                code=123, name="Test Station", lat=49.0, long=-123.0, elevation=500.0
            ),
        ]

        # Raw daily with None station data (should be filtered by is_station_valid)
        raw_dailies = [
            {
                "stationData": None,
                "temperature": 15.0,
                "recordType": {"id": "ACTUAL"},
            },
        ]

        with patch(
            "app.sfms.temperature_interpolation.fetch_raw_dailies_for_all_stations",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = raw_dailies

            result = await fetch_station_temperatures(
                mock_session, headers, time_of_interest, stations
            )

            assert len(result) == 0

    @pytest.mark.anyio
    async def test_fetch_handles_exception_gracefully(self):
        """Test that exceptions during processing are handled."""
        mock_session = AsyncMock()
        headers = {"Authorization": "Bearer test_token"}
        time_of_interest = datetime(2024, 1, 15, 20, 0, 0, tzinfo=timezone.utc)

        stations = [
            WeatherStation(
                code=123, name="Test Station 1", lat=49.0, long=-123.0, elevation=500.0
            ),
            WeatherStation(
                code=456, name="Test Station 2", lat=50.0, long=-124.0, elevation=1000.0
            ),
        ]

        # One valid, one that will cause an error
        raw_dailies = [
            {
                "stationData": {
                    "stationCode": 123,
                    "displayLabel": "Test Station 1",
                    "stationStatus": {"id": "ACTIVE"},
                    "latitude": 49.0,
                    "longitude": -123.0,
                },
                "temperature": 15.0,
                "recordType": {"id": "ACTUAL"},
            },
            {
                "stationData": {
                    "stationCode": 456,
                    "displayLabel": "Test Station 2",
                    "stationStatus": {"id": "ACTIVE"},
                    "latitude": 50.0,
                    "longitude": -124.0,
                },
                "temperature": "invalid",  # This will cause a conversion error
                "recordType": {"id": "ACTUAL"},
            },
        ]

        with patch(
            "app.sfms.temperature_interpolation.fetch_raw_dailies_for_all_stations",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = raw_dailies

            result = await fetch_station_temperatures(
                mock_session, headers, time_of_interest, stations
            )

            # Should still get the first valid station
            assert len(result) == 1
            assert result[0].code == 123


class TestInterpolateTemperatureToRaster:
    """Tests for interpolate_temperature_to_raster function."""

    @pytest.mark.anyio
    async def test_interpolate_basic_success(self):
        """Test successful raster interpolation."""
        stations = [
            StationTemperature(code=1, lat=49.0, lon=-123.0, elevation=0, temperature=15.0),
            StationTemperature(code=2, lat=49.1, lon=-123.1, elevation=500, temperature=12.0),
        ]

        # Create mock GDAL datasets
        mock_ref_ds = Mock()
        mock_ref_ds.GetGeoTransform.return_value = (0, 1, 0, 50, 0, -1)
        mock_ref_ds.GetProjection.return_value = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]]]'
        mock_ref_ds.RasterXSize = 10
        mock_ref_ds.RasterYSize = 10

        mock_dem_band = Mock()
        mock_dem_band.ReadAsArray.return_value = np.full((10, 10), 100.0)
        mock_dem_band.GetNoDataValue.return_value = -9999.0

        mock_dem_ds = Mock()
        mock_dem_ds.GetRasterBand.return_value = mock_dem_band

        mock_output_ds = Mock()
        mock_output_ds.export_to_geotiff = Mock()
        mock_output_ds.__enter__ = Mock(return_value=mock_output_ds)
        mock_output_ds.__exit__ = Mock(return_value=False)

        # Mock WPSDataset
        with patch("app.sfms.temperature_interpolation.WPSDataset") as mock_wps_dataset:
            # Setup context managers
            mock_ref_ctx = MagicMock()
            mock_ref_ctx.__enter__ = Mock(return_value=Mock(ds=mock_ref_ds))
            mock_ref_ctx.__exit__ = Mock(return_value=False)

            mock_dem_ctx = MagicMock()
            mock_dem_ctx.__enter__ = Mock(return_value=Mock(ds=mock_dem_ds))
            mock_dem_ctx.__exit__ = Mock(return_value=False)

            mock_wps_dataset.side_effect = [mock_ref_ctx, mock_dem_ctx]
            mock_wps_dataset.from_array.return_value = mock_output_ds

            result = await interpolate_temperature_to_raster(
                stations, "/path/to/ref.tif", "/path/to/dem.tif", "/path/to/output.tif"
            )

            assert result == "/path/to/output.tif"
            mock_output_ds.export_to_geotiff.assert_called_once_with("/path/to/output.tif")

    @pytest.mark.anyio
    async def test_interpolate_skips_nodata_cells(self):
        """Test that cells with NoData elevation are skipped."""
        stations = [
            StationTemperature(code=1, lat=49.0, lon=-123.0, elevation=0, temperature=15.0),
        ]

        # Create DEM with NoData values
        dem_data = np.full((5, 5), 100.0)
        dem_data[2, 2] = -9999.0  # NoData cell

        mock_ref_ds = Mock()
        mock_ref_ds.GetGeoTransform.return_value = (0, 1, 0, 50, 0, -1)
        mock_ref_ds.GetProjection.return_value = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]]]'
        mock_ref_ds.RasterXSize = 5
        mock_ref_ds.RasterYSize = 5

        mock_dem_band = Mock()
        mock_dem_band.ReadAsArray.return_value = dem_data
        mock_dem_band.GetNoDataValue.return_value = -9999.0

        mock_dem_ds = Mock()
        mock_dem_ds.GetRasterBand.return_value = mock_dem_band

        mock_output_ds = Mock()
        mock_output_ds.export_to_geotiff = Mock()
        mock_output_ds.__enter__ = Mock(return_value=mock_output_ds)
        mock_output_ds.__exit__ = Mock(return_value=False)

        with patch("app.sfms.temperature_interpolation.WPSDataset") as mock_wps_dataset:
            mock_ref_ctx = MagicMock()
            mock_ref_ctx.__enter__ = Mock(return_value=Mock(ds=mock_ref_ds))
            mock_ref_ctx.__exit__ = Mock(return_value=False)

            mock_dem_ctx = MagicMock()
            mock_dem_ctx.__enter__ = Mock(return_value=Mock(ds=mock_dem_ds))
            mock_dem_ctx.__exit__ = Mock(return_value=False)

            mock_wps_dataset.side_effect = [mock_ref_ctx, mock_dem_ctx]
            mock_wps_dataset.from_array.return_value = mock_output_ds

            result = await interpolate_temperature_to_raster(
                stations, "/path/to/ref.tif", "/path/to/dem.tif", "/path/to/output.tif"
            )

            assert result == "/path/to/output.tif"

    @pytest.mark.anyio
    async def test_interpolate_filters_stations_without_sea_level_temp(self):
        """Test that stations without sea_level_temp are filtered."""
        stations = [
            StationTemperature(code=1, lat=49.0, lon=-123.0, elevation=0, temperature=15.0),
            StationTemperature(code=2, lat=49.1, lon=-123.1, elevation=500, temperature=12.0),
        ]

        # Only adjust first station
        adjust_temperature_to_sea_level(stations[0])
        # stations[1] will have None sea_level_temp

        mock_ref_ds = Mock()
        mock_ref_ds.GetGeoTransform.return_value = (0, 1, 0, 50, 0, -1)
        mock_ref_ds.GetProjection.return_value = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]]]'
        mock_ref_ds.RasterXSize = 5
        mock_ref_ds.RasterYSize = 5

        mock_dem_band = Mock()
        mock_dem_band.ReadAsArray.return_value = np.full((5, 5), 100.0)
        mock_dem_band.GetNoDataValue.return_value = None

        mock_dem_ds = Mock()
        mock_dem_ds.GetRasterBand.return_value = mock_dem_band

        mock_output_ds = Mock()
        mock_output_ds.export_to_geotiff = Mock()
        mock_output_ds.__enter__ = Mock(return_value=mock_output_ds)
        mock_output_ds.__exit__ = Mock(return_value=False)

        with patch("app.sfms.temperature_interpolation.WPSDataset") as mock_wps_dataset:
            mock_ref_ctx = MagicMock()
            mock_ref_ctx.__enter__ = Mock(return_value=Mock(ds=mock_ref_ds))
            mock_ref_ctx.__exit__ = Mock(return_value=False)

            mock_dem_ctx = MagicMock()
            mock_dem_ctx.__enter__ = Mock(return_value=Mock(ds=mock_dem_ds))
            mock_dem_ctx.__exit__ = Mock(return_value=False)

            mock_wps_dataset.side_effect = [mock_ref_ctx, mock_dem_ctx]
            mock_wps_dataset.from_array.return_value = mock_output_ds

            result = await interpolate_temperature_to_raster(
                stations, "/path/to/ref.tif", "/path/to/dem.tif", "/path/to/output.tif"
            )

            assert result == "/path/to/output.tif"


    @pytest.mark.anyio
    async def test_interpolate_with_actual_loop_execution(self):
        """Test interpolation with actual loop execution to cover lines 229-232."""
        # Station at exactly (49.0, -123.0)
        stations = [
            StationTemperature(code=1, lat=49.0, lon=-123.0, elevation=100, temperature=15.0),
        ]

        # Adjust to sea level
        for station in stations:
            adjust_temperature_to_sea_level(station)

        # Create very small test arrays (2x2) to allow actual loop execution
        dem_data = np.array([[100.0, 200.0], [150.0, 250.0]], dtype=np.float32)

        mock_ref_ds = Mock()
        # Geotransform: (x_origin, pixel_width, 0, y_origin, 0, pixel_height)
        # Place raster cells very close to station location (49.0, -123.0)
        # Cell centers will be at approximately: (49.05, -123.05), (49.05, -123.01), (49.01, -123.05), (49.01, -123.01)
        mock_ref_ds.GetGeoTransform.return_value = (-123.1, 0.05, 0, 49.1, 0, -0.05)
        mock_ref_ds.GetProjection.return_value = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]]]'
        mock_ref_ds.RasterXSize = 2
        mock_ref_ds.RasterYSize = 2

        mock_dem_band = Mock()
        mock_dem_band.ReadAsArray.return_value = dem_data
        mock_dem_band.GetNoDataValue.return_value = None

        mock_dem_ds = Mock()
        mock_dem_ds.GetRasterBand.return_value = mock_dem_band

        mock_output_ds = Mock()
        mock_output_ds.export_to_geotiff = Mock()
        mock_output_ds.__enter__ = Mock(return_value=mock_output_ds)
        mock_output_ds.__exit__ = Mock(return_value=False)

        # Track the array that gets passed to from_array
        captured_array = None

        def capture_from_array(array, **kwargs):
            nonlocal captured_array
            captured_array = array
            return mock_output_ds

        # Mock coordinate transformation to return points near station (49.0, -123.0)
        mock_transform = Mock()
        # Return coordinates very close to the station for all pixels
        mock_transform.TransformPoint.return_value = (-123.0, 49.0, 0)

        with patch("app.sfms.temperature_interpolation.WPSDataset") as mock_wps_dataset, \
             patch("app.sfms.temperature_interpolation.osr") as mock_osr:

            # Mock osr module
            mock_source_srs = Mock()
            mock_osr.SpatialReference.return_value = mock_source_srs
            mock_osr.CoordinateTransformation.return_value = mock_transform

            mock_ref_ctx = MagicMock()
            mock_ref_ctx.__enter__ = Mock(return_value=Mock(ds=mock_ref_ds))
            mock_ref_ctx.__exit__ = Mock(return_value=False)

            mock_dem_ctx = MagicMock()
            mock_dem_ctx.__enter__ = Mock(return_value=Mock(ds=mock_dem_ds))
            mock_dem_ctx.__exit__ = Mock(return_value=False)

            mock_wps_dataset.side_effect = [mock_ref_ctx, mock_dem_ctx]
            mock_wps_dataset.from_array = Mock(side_effect=capture_from_array)

            # Run interpolation - this will execute the nested loops and lines 229-232
            result = await interpolate_temperature_to_raster(
                stations, "/path/to/ref.tif", "/path/to/dem.tif", "/path/to/output.tif"
            )

            assert result == "/path/to/output.tif"

            # Verify that the output array was created and has non-NoData values
            assert captured_array is not None
            assert captured_array.shape == (2, 2)
            # At least some cells should have been interpolated (not all -9999)
            non_nodata_count = np.sum(captured_array != -9999.0)
            assert non_nodata_count > 0, "Expected some cells to be interpolated"


class TestGetDemPath:
    """Tests for get_dem_path function."""

    @pytest.mark.anyio
    async def test_get_dem_path_returns_correct_format(self):
        """Test that get_dem_path returns correct S3 path format."""
        with patch("app.sfms.temperature_interpolation.config") as mock_config:
            mock_config.get.side_effect = lambda key: {
                "OBJECT_STORE_BUCKET": "test-bucket",
                "DEM_NAME": "test-dem.tif",
            }.get(key)

            result = await get_dem_path()

            assert result == "/vsis3/test-bucket/dem/mosaics/test-dem.tif"

    @pytest.mark.anyio
    async def test_get_dem_path_with_different_config(self):
        """Test get_dem_path with different config values."""
        with patch("app.sfms.temperature_interpolation.config") as mock_config:
            mock_config.get.side_effect = lambda key: {
                "OBJECT_STORE_BUCKET": "production-bucket",
                "DEM_NAME": "bc_dem_25m.tif",
            }.get(key)

            result = await get_dem_path()

            assert result == "/vsis3/production-bucket/dem/mosaics/bc_dem_25m.tif"


class TestIntegrationScenario:
    """Integration tests simulating real-world scenarios."""

    def test_full_workflow_simple(self):
        """Test the full workflow with simple data."""
        # Create stations at different elevations
        stations = [
            StationTemperature(
                code=1, lat=49.0, lon=-123.0, elevation=0, temperature=15.0
            ),  # Sea level, 15°C
            StationTemperature(
                code=2, lat=49.1, lon=-123.1, elevation=500, temperature=10.0
            ),  # 500m, 10°C
            StationTemperature(
                code=3, lat=49.2, lon=-123.2, elevation=1000, temperature=5.0
            ),  # 1000m, 5°C
        ]

        # Adjust all to sea level
        for station in stations:
            adjust_temperature_to_sea_level(station)

        # Verify sea level adjustments
        # Station 1: 15 + 0 = 15°C
        assert stations[0].sea_level_temp == pytest.approx(15.0, rel=1e-6)

        # Station 2: 10 + (500 * 0.0098) = 10 + 4.9 = 14.9°C
        assert stations[1].sea_level_temp == pytest.approx(14.9, rel=1e-6)

        # Station 3: 5 + (1000 * 0.0098) = 5 + 9.8 = 14.8°C
        assert stations[2].sea_level_temp == pytest.approx(14.8, rel=1e-6)

        # Prepare lists for IDW
        lats = [s.lat for s in stations]
        lons = [s.lon for s in stations]
        values = [s.sea_level_temp for s in stations]

        # Interpolate at a point
        interpolated = idw_interpolation(49.1, -123.1, lats, lons, values)
        assert interpolated is not None

        # Adjust back to elevation (e.g., 250m)
        final_temp = adjust_temperature_to_elevation(interpolated, 250)

        # Should be reasonable (between 5-15°C range)
        assert 5.0 <= final_temp <= 15.0
