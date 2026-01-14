"""
Generic spatial interpolation utilities.

This module provides reusable functions for spatial interpolation of point data,
particularly useful for weather station observations (temperature, dew point, wind, etc.).
"""

import logging
from dataclasses import dataclass
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class NearbyStation:
    """A station within the search radius with its distance and value."""

    distance: float  # Distance from target point in meters
    value: float  # Measured value at the station

# IDW parameters
IDW_POWER = 2.0  # Standard IDW power parameter
SEARCH_RADIUS = 500000  # 500km search radius in meters
MAX_STATIONS = 12  # Maximum number of nearest stations to use


def haversine_distance(
    lat1: float | np.ndarray,
    lon1: float | np.ndarray,
    lat2: float | np.ndarray,
    lon2: float | np.ndarray,
) -> float | np.ndarray:
    """
    Calculate great circle distance(s) between points on Earth using the Haversine formula.

    This unified function handles three cases:
    - Scalar to scalar: returns a single distance (float)
    - Scalar to array: returns distances from one point to many (1D array)
    - Array to array: returns distance matrix (2D array) where result[i,j] is
      distance from point i in (lat1, lon1) to point j in (lat2, lon2)

    :param lat1: Latitude(s) of first point(s) in degrees (scalar or array)
    :param lon1: Longitude(s) of first point(s) in degrees (scalar or array)
    :param lat2: Latitude(s) of second point(s) in degrees (scalar or array)
    :param lon2: Longitude(s) of second point(s) in degrees (scalar or array)
    :return: Distance(s) in meters (scalar, 1D array, or 2D array)
    """
    lat1_is_array = isinstance(lat1, np.ndarray)
    lat2_is_array = isinstance(lat2, np.ndarray)

    # Case 1: Both arrays -> distance matrix (N x M)
    if lat1_is_array and lat2_is_array:
        lat1_rad = np.radians(lat1)[:, np.newaxis]
        lon1_rad = np.radians(lon1)[:, np.newaxis]
        lat2_rad = np.radians(lat2)[np.newaxis, :]
        lon2_rad = np.radians(lon2)[np.newaxis, :]
    # Case 2: First is scalar, second is array -> 1D array of distances
    elif lat2_is_array:
        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)
    # Case 3: Both scalars (or first is array, second is scalar - treated same way)
    else:
        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)

    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))

    # Earth radius in meters
    radius = 6371000
    result = radius * c

    # Return scalar for scalar-to-scalar case
    if not lat1_is_array and not lat2_is_array:
        return float(result)
    return result




def collect_nearby_stations(
    target_lat: float,
    target_lon: float,
    point_lats: List[float],
    point_lons: List[float],
    point_values: List[float],
    search_radius: float,
) -> List[NearbyStation]:
    """
    Collect stations within search radius with their distances and values.

    Uses vectorized NumPy operations for fast computation.

    :param target_lat: Latitude of target point (degrees)
    :param target_lon: Longitude of target point (degrees)
    :param point_lats: List of latitudes for data points (degrees)
    :param point_lons: List of longitudes for data points (degrees)
    :param point_values: List of values at each data point
    :param search_radius: Maximum distance to consider points (meters)
    :return: List of NearbyStation objects for stations within radius
    """
    # Filter out None values first (before converting to NumPy)
    valid_stations = [
        (lat, lon, val)
        for lat, lon, val in zip(point_lats, point_lons, point_values)
        if val is not None
    ]

    # If no valid stations, return empty list
    if not valid_stations:
        return []

    # Convert to NumPy arrays
    lats_array = np.array([s[0] for s in valid_stations])
    lons_array = np.array([s[1] for s in valid_stations])
    values_array = np.array([s[2] for s in valid_stations])

    # Calculate distances to all stations at once (vectorized)
    distances = haversine_distance(target_lat, target_lon, lats_array, lons_array)
    assert isinstance(distances, np.ndarray)

    # Filter stations within search radius using boolean indexing
    within_radius = distances <= search_radius
    distances_filtered = distances[within_radius]
    values_filtered = values_array[within_radius]

    # Convert to list of NearbyStation objects
    stations_in_range = [
        NearbyStation(distance=float(dist), value=float(val))
        for dist, val in zip(distances_filtered, values_filtered)
    ]

    return stations_in_range


def idw_interpolation(
    target_lat: float,
    target_lon: float,
    point_lats: List[float],
    point_lons: List[float],
    point_values: List[float],
    power: float = IDW_POWER,
    search_radius: float = SEARCH_RADIUS,
    max_stations: Optional[int] = MAX_STATIONS,
) -> Optional[float]:
    """
    Perform Inverse Distance Weighting (IDW) interpolation for a single point.

    IDW is a deterministic spatial interpolation method that estimates values at
    unsampled locations based on a weighted average of nearby observations. Weights
    are inversely proportional to distance raised to a power.

    Formula: value = Σ(w_i * v_i) / Σ(w_i)
    where w_i = 1 / (distance_i ^ power)

    :param target_lat: Latitude of point to interpolate (degrees)
    :param target_lon: Longitude of point to interpolate (degrees)
    :param point_lats: List of latitudes for data points (degrees)
    :param point_lons: List of longitudes for data points (degrees)
    :param point_values: List of values at each data point
    :param power: IDW power parameter (default 2.0, higher = more local influence)
    :param search_radius: Maximum distance to consider points (meters)
    :param max_stations: Maximum number of nearest stations to use (default 12)
    :return: Interpolated value or None if no valid points in range

    Examples:
        >>> # Simple interpolation between two points
        >>> lats = [49.0, 50.0]
        >>> lons = [-123.0, -123.0]
        >>> temps = [15.0, 20.0]
        >>> result = idw_interpolation(49.5, -123.0, lats, lons, temps)
        >>> # result will be weighted average closer to midpoint

        >>> # Handle points outside search radius
        >>> result = idw_interpolation(60.0, -130.0, lats, lons, temps, search_radius=10000)
        >>> # result will be None (no points within 10km)

        >>> # Limit to nearest N stations
        >>> result = idw_interpolation(49.5, -123.0, lats, lons, temps, max_stations=5)
        >>> # result will use only the 5 nearest stations
    """
    # Validate inputs
    if not point_lats or len(point_lats) != len(point_lons) or len(point_lats) != len(point_values):
        logger.warning(
            "Invalid input lengths: lats=%d, lons=%d, values=%d",
            len(point_lats) if point_lats else 0,
            len(point_lons) if point_lons else 0,
            len(point_values) if point_values else 0,
        )
        return None

    # Collect stations within search radius with their distances
    stations_in_range = collect_nearby_stations(
        target_lat, target_lon, point_lats, point_lons, point_values, search_radius
    )

    # Check if we found any points in range
    if not stations_in_range:
        logger.debug(
            "No valid points found within search radius %.0fm of target (%.4f, %.4f)",
            search_radius,
            target_lat,
            target_lon,
        )
        return None

    # Sort by distance and take only the nearest N stations
    stations_in_range.sort(key=lambda station: station.distance)

    # Handle exact match case (distance < 1m) to avoid division by zero
    if stations_in_range[0].distance < 1.0:
        logger.debug("Target point within 1m of data point, returning exact value")
        return stations_in_range[0].value

    if max_stations is not None and len(stations_in_range) > max_stations:
        stations_in_range = stations_in_range[:max_stations]

    # Extract distances and values as NumPy arrays for vectorized computation
    distances = np.array([station.distance for station in stations_in_range])
    values = np.array([station.value for station in stations_in_range])

    # Calculate IDW weights (vectorized)
    weights = 1.0 / (distances**power)

    # Calculate weighted average (vectorized)
    interpolated_value = np.sum(weights * values) / np.sum(weights)

    logger.debug(
        "IDW interpolated value %.2f from %d points at (%.4f, %.4f)",
        float(interpolated_value),
        len(stations_in_range),
        target_lat,
        target_lon,
    )

    return float(interpolated_value)


def idw_interpolation_batch(
    distances_matrix: np.ndarray,
    point_values: np.ndarray,
    power: float = IDW_POWER,
    search_radius: float = SEARCH_RADIUS,
    max_stations: Optional[int] = MAX_STATIONS,
) -> np.ndarray:
    """
    Perform IDW interpolation for multiple points using pre-computed distance matrix.

    This is much faster than calling idw_interpolation() in a loop because distances
    are pre-computed.

    :param distances_matrix: Array of shape (N, M) where N is number of target points
                           and M is number of data points. distances_matrix[i, j] is
                           distance from target i to data point j.
    :param point_values: Array of M values at each data point
    :param power: IDW power parameter (default 2.0)
    :param search_radius: Maximum distance to consider points (meters)
    :param max_stations: Maximum number of nearest stations to use (default 12)
    :return: Array of N interpolated values (or np.nan where interpolation failed)
    """
    n_targets = distances_matrix.shape[0]
    results = np.full(n_targets, np.nan, dtype=np.float64)

    for i in range(n_targets):
        distances = distances_matrix[i]

        # Filter stations within search radius
        within_radius = distances <= search_radius
        valid_distances = distances[within_radius]
        valid_values = point_values[within_radius]

        if len(valid_distances) == 0:
            continue

        # Check for exact match (< 1m)
        min_dist_idx = np.argmin(valid_distances)
        if valid_distances[min_dist_idx] < 1.0:
            results[i] = valid_values[min_dist_idx]
            continue

        # Sort by distance and take top N
        if max_stations is not None and len(valid_distances) > max_stations:
            sorted_indices = np.argsort(valid_distances)[:max_stations]
            valid_distances = valid_distances[sorted_indices]
            valid_values = valid_values[sorted_indices]

        # Calculate IDW weights
        weights = 1.0 / (valid_distances**power)

        # Calculate weighted average
        results[i] = np.sum(weights * valid_values) / np.sum(weights)

    return results
