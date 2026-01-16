"""
Unit tests for spatial interpolation utilities.
"""

import numpy as np
import pytest
from wps_shared.geospatial.spatial_interpolation import (
    idw_interpolation,
    _make_idw_weights,
    IDW_POWER,
    SEARCH_RADIUS,
    MAX_STATIONS,
    EARTH_RADIUS,
)


class TestConstants:
    """Tests for module constants."""

    def test_idw_power_default(self):
        """Test that IDW power is standard value."""
        assert IDW_POWER == pytest.approx(2.0)

    def test_search_radius_default(self):
        """Test that search radius is 500km."""
        assert SEARCH_RADIUS == 500000  # 500km in meters

    def test_max_stations_default(self):
        """Test that max stations is 12."""
        assert MAX_STATIONS == 12


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

    def test_max_stations_limit(self):
        """Test that max_stations limits the number of stations used."""
        # Create 20 stations in a line
        lats = [49.0 + i * 0.1 for i in range(20)]
        lons = [-123.0] * 20
        values = [float(i) for i in range(20)]

        # Query at first station location with max_stations=5
        # Should only use the 5 nearest stations (stations 0-4)
        result = idw_interpolation(49.0, -123.0, lats, lons, values, max_stations=5)

        # Result should be very close to 0.0 (the first station's value)
        # Since we're at the exact location, it should return that value
        assert result == pytest.approx(0.0, rel=1e-6)

        # Query at a point between stations with max_stations=3
        result = idw_interpolation(49.25, -123.0, lats, lons, values, max_stations=3)

        # Should use only stations 2, 3, 4 (the 3 nearest to 49.25)
        # Result should be weighted average of those, close to 2.5
        assert result is not None
        assert 2.0 < result < 3.0


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


class TestMakeIdwWeights:
    """Tests for _make_idw_weights helper function."""

    def test_basic_idw_weights(self):
        """Test basic IDW weight calculation with power=2."""
        weights_fn = _make_idw_weights(power=2.0, max_stations=None)
        distances = [np.array([1.0, 2.0, 4.0])]

        result = weights_fn(distances)

        # Weights should be 1/d^2: [1.0, 0.25, 0.0625]
        assert len(result) == 1
        assert result[0] == pytest.approx([1.0, 0.25, 0.0625])

    def test_power_parameter(self):
        """Test that power parameter affects weights correctly."""
        weights_fn_p1 = _make_idw_weights(power=1.0, max_stations=None)
        weights_fn_p3 = _make_idw_weights(power=3.0, max_stations=None)
        distances = [np.array([2.0, 4.0])]

        result_p1 = weights_fn_p1(distances)
        result_p3 = weights_fn_p3(distances)

        # power=1: [1/2, 1/4] = [0.5, 0.25]
        assert result_p1[0] == pytest.approx([0.5, 0.25])
        # power=3: [1/8, 1/64] = [0.125, 0.015625]
        assert result_p3[0] == pytest.approx([0.125, 0.015625])

    def test_max_stations_limit(self):
        """Test that max_stations limits which stations get non-zero weights."""
        weights_fn = _make_idw_weights(power=2.0, max_stations=2)
        # Distances: 1.0, 3.0, 2.0 - sorted: 1.0, 2.0, 3.0
        distances = [np.array([1.0, 3.0, 2.0])]

        result = weights_fn(distances)

        # Only 2 nearest (indices 0 and 2) should have non-zero weights
        assert result[0][0] > 0  # distance 1.0 - nearest
        assert result[0][1] == pytest.approx(0)  # distance 3.0 - excluded
        assert result[0][2] > 0  # distance 2.0 - second nearest

    def test_max_stations_none(self):
        """Test that max_stations=None uses all stations."""
        weights_fn = _make_idw_weights(power=2.0, max_stations=None)
        distances = [np.array([1.0, 2.0, 3.0, 4.0, 5.0])]

        result = weights_fn(distances)

        # All should have non-zero weights
        assert all(w > 0 for w in result[0])

    def test_exact_match_threshold(self):
        """Test that exact matches (< 1m) get exclusive weight."""
        weights_fn = _make_idw_weights(power=2.0, max_stations=None)
        # First distance is < 1m in radians (1m / EARTH_RADIUS ≈ 1.57e-7)
        exact_match_dist = 0.5 / EARTH_RADIUS
        distances = [np.array([exact_match_dist, 1.0, 2.0])]

        result = weights_fn(distances)

        # Only the exact match should have weight
        assert result[0][0] == pytest.approx(1.0)
        assert result[0][1] == pytest.approx(0.0)
        assert result[0][2] == pytest.approx(0.0)

    def test_multiple_query_points(self):
        """Test weight calculation for multiple query points."""
        weights_fn = _make_idw_weights(power=2.0, max_stations=None)
        distances = [
            np.array([1.0, 2.0]),
            np.array([2.0, 4.0]),
        ]

        result = weights_fn(distances)

        assert len(result) == 2
        assert result[0] == pytest.approx([1.0, 0.25])
        assert result[1] == pytest.approx([0.25, 0.0625])

    def test_empty_distances(self):
        """Test handling of empty distance array."""
        weights_fn = _make_idw_weights(power=2.0, max_stations=None)
        distances = [np.array([])]

        result = weights_fn(distances)

        assert len(result) == 1
        assert len(result[0]) == 0

    def test_single_station(self):
        """Test with only one station."""
        weights_fn = _make_idw_weights(power=2.0, max_stations=None)
        distances = [np.array([5.0])]

        result = weights_fn(distances)

        assert len(result[0]) == 1
        assert result[0][0] == pytest.approx(1.0 / 25.0)

    def test_max_stations_greater_than_available(self):
        """Test max_stations when fewer stations available than limit."""
        weights_fn = _make_idw_weights(power=2.0, max_stations=10)
        distances = [np.array([1.0, 2.0, 3.0])]  # Only 3 stations

        result = weights_fn(distances)

        # All 3 should have non-zero weights
        assert all(w > 0 for w in result[0])
