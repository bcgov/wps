"""
Unit tests for spatial interpolation utilities.
"""

import pytest
from wps_shared.geospatial.spatial_interpolation import (
    haversine_distance,
    idw_interpolation,
    IDW_POWER,
    SEARCH_RADIUS,
)


class TestConstants:
    """Tests for module constants."""

    def test_idw_power_default(self):
        """Test that IDW power is standard value."""
        assert IDW_POWER == pytest.approx(2.0)

    def test_search_radius_default(self):
        """Test that search radius is 200km."""
        assert SEARCH_RADIUS == 200000  # 200km in meters


class TestHaversineDistance:
    """Tests for Haversine distance calculation."""

    def test_same_point(self):
        """Test that distance between same point is zero."""
        lat, lon = 49.0, -123.0
        distance = haversine_distance(lat, lon, lat, lon)
        assert distance == pytest.approx(0.0, abs=1.0)

    def test_known_distance_vancouver_seattle(self):
        """Test with known distance between Vancouver and Seattle."""
        vancouver_lat, vancouver_lon = 49.2827, -123.1207
        seattle_lat, seattle_lon = 47.6062, -122.3321

        distance = haversine_distance(vancouver_lat, vancouver_lon, seattle_lat, seattle_lon)

        # Should be approximately 195 km (allow 5% tolerance)
        assert distance == pytest.approx(195000, rel=0.05)

    def test_equator_degree(self):
        """Test distance of 1 degree longitude at equator."""
        distance = haversine_distance(0.0, 0.0, 0.0, 1.0)
        # 1 degree at equator ≈ 111.32 km
        assert distance == pytest.approx(111320, rel=0.01)

    def test_north_south_distance(self):
        """Test north-south distance (latitude change only)."""
        # 1 degree latitude ≈ 111 km everywhere
        distance = haversine_distance(49.0, -123.0, 50.0, -123.0)
        assert distance == pytest.approx(111000, rel=0.01)


class TestIDWInterpolation:
    """Tests for Inverse Distance Weighting interpolation."""

    def test_exact_location_match(self):
        """Test that IDW returns exact value when target is at data point."""
        lats = [49.0, 50.0]
        lons = [-123.0, -124.0]
        values = [15.0, 20.0]

        # Query at exact first point location
        result = idw_interpolation(49.0, -123.0, lats, lons, values)

        assert result == pytest.approx(15.0, rel=1e-6)

    def test_interpolation_between_points(self):
        """Test IDW interpolation between two points."""
        lats = [49.0, 50.0]
        lons = [-123.0, -123.0]
        values = [10.0, 20.0]

        # Query at midpoint
        result = idw_interpolation(49.5, -123.0, lats, lons, values)

        # Should be weighted average between the two
        assert result is not None
        assert 10.0 < result < 20.0

    def test_empty_input(self):
        """Test that IDW returns None with empty input."""
        result = idw_interpolation(49.0, -123.0, [], [], [])
        assert result is None

    def test_mismatched_lengths(self):
        """Test that IDW returns None with mismatched input lengths."""
        result = idw_interpolation(49.0, -123.0, [49.0], [-123.0, -124.0], [15.0])
        assert result is None

    def test_none_values_filtered(self):
        """Test that None values are filtered out."""
        lats = [49.0, 50.0, 51.0]
        lons = [-123.0, -124.0, -125.0]
        values = [15.0, None, 20.0]  # Middle value is None

        result = idw_interpolation(49.5, -123.5, lats, lons, values)

        # Should still work with only two valid values
        assert result is not None

    def test_outside_search_radius(self):
        """Test that IDW returns None when all points outside search radius."""
        lats = [49.0]
        lons = [-123.0]
        values = [15.0]

        # Query far away with small search radius
        result = idw_interpolation(52.0, -128.0, lats, lons, values, search_radius=10000)
        assert result is None

    def test_within_search_radius(self):
        """Test that IDW works when points are within search radius."""
        lats = [49.0]
        lons = [-123.0]
        values = [15.0]

        # Query nearby with large search radius
        result = idw_interpolation(49.1, -123.0, lats, lons, values, search_radius=50000)
        assert result is not None

    def test_custom_power_parameter(self):
        """Test IDW with custom power parameter."""
        lats = [49.0, 50.0]
        lons = [-123.0, -123.0]
        values = [10.0, 20.0]

        # Higher power = more weight to nearby points
        result_power_1 = idw_interpolation(49.2, -123.0, lats, lons, values, power=1.0)
        result_power_3 = idw_interpolation(49.2, -123.0, lats, lons, values, power=3.0)

        assert result_power_1 is not None
        assert result_power_3 is not None
        # With power=3, nearby point has more influence
        assert result_power_3 < result_power_1

    def test_single_point(self):
        """Test IDW with single valid point."""
        lats = [49.0]
        lons = [-123.0]
        values = [15.0]

        result = idw_interpolation(49.5, -123.0, lats, lons, values)

        # Should return the single point's value
        assert result == pytest.approx(15.0, abs=0.1)

    def test_all_none_values(self):
        """Test that IDW returns None when all values are None."""
        lats = [49.0, 50.0]
        lons = [-123.0, -124.0]
        values = [None, None]

        result = idw_interpolation(49.5, -123.5, lats, lons, values)
        assert result is None

    def test_three_points_weighted_average(self):
        """Test IDW with three points forming a triangle."""
        lats = [49.0, 50.0, 49.5]
        lons = [-123.0, -123.0, -124.0]
        values = [10.0, 20.0, 15.0]

        # Query near the center
        result = idw_interpolation(49.5, -123.3, lats, lons, values)

        assert result is not None
        # Should be weighted average, somewhere in the middle
        assert 10.0 < result < 20.0


class TestIDWEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_zero_distance_threshold(self):
        """Test that points within 1 meter are considered exact matches."""
        lats = [49.0]
        lons = [-123.0]
        values = [15.0]

        # Query 0.5 meters away (using very small lat/lon difference)
        # This should be caught by the < 1.0 meter threshold
        result = idw_interpolation(49.0000001, -123.0000001, lats, lons, values)

        assert result == pytest.approx(15.0, rel=1e-6)

    def test_negative_values(self):
        """Test that negative values work correctly."""
        lats = [49.0, 50.0]
        lons = [-123.0, -124.0]
        values = [-5.0, -10.0]

        result = idw_interpolation(49.5, -123.5, lats, lons, values)

        assert result is not None
        assert -10.0 <= result <= -5.0

    def test_large_values(self):
        """Test with large numeric values."""
        lats = [49.0, 50.0]
        lons = [-123.0, -124.0]
        values = [1000.0, 2000.0]

        result = idw_interpolation(49.5, -123.5, lats, lons, values)

        assert result is not None
        assert 1000.0 < result < 2000.0
