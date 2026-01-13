"""
Unit tests for temperature interpolation module.
"""

import pytest
from datetime import datetime, timezone
from wps_shared.schemas.sfms import StationTemperature
from wps_shared.geospatial.spatial_interpolation import (
    haversine_distance,
    idw_interpolation,
)
from app.sfms.temperature_interpolation import (
    adjust_temperature_to_sea_level,
    adjust_temperature_to_elevation,
    get_interpolated_temp_key,
    DRY_ADIABATIC_LAPSE_RATE,
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

    def test_interpolated_temp_key_format(self):
        """Test that interpolated temperature key has correct format."""
        dt = datetime(2024, 1, 15, 20, 0, 0, tzinfo=timezone.utc)
        key = get_interpolated_temp_key(dt)

        expected = "sfms/interpolated/temperature/2024/01/15/temperature_20240115.tif"
        assert key == expected

    def test_interpolated_temp_key_different_dates(self):
        """Test key generation for different dates."""
        # Test December (month 12)
        dt = datetime(2024, 12, 31, 20, 0, 0, tzinfo=timezone.utc)
        key = get_interpolated_temp_key(dt)
        assert key == "sfms/interpolated/temperature/2024/12/31/temperature_20241231.tif"

        # Test single digit month
        dt = datetime(2024, 3, 5, 20, 0, 0, tzinfo=timezone.utc)
        key = get_interpolated_temp_key(dt)
        assert key == "sfms/interpolated/temperature/2024/03/05/temperature_20240305.tif"


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
