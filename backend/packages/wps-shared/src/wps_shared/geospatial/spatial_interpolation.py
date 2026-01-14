"""
Generic spatial interpolation utilities.

This module provides reusable functions for spatial interpolation of point data,
particularly useful for weather station observations (temperature, dew point, wind, etc.).
"""

import logging
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)

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



def idw_interpolation(
    target_lat: float | np.ndarray,
    target_lon: float | np.ndarray,
    point_lats: List[float] | np.ndarray,
    point_lons: List[float] | np.ndarray,
    point_values: List[float] | np.ndarray,
    power: float = IDW_POWER,
    search_radius: float = SEARCH_RADIUS,
    max_stations: Optional[int] = MAX_STATIONS,
) -> Optional[float] | np.ndarray:
    """
    Perform Inverse Distance Weighting (IDW) interpolation.

    Handles both single point and batch interpolation:
    - Scalar target_lat/lon: returns Optional[float]
    - Array target_lat/lon: returns np.ndarray of interpolated values

    IDW is a deterministic spatial interpolation method that estimates values at
    unsampled locations based on a weighted average of nearby observations. Weights
    are inversely proportional to distance raised to a power.

    Formula: value = Σ(w_i * v_i) / Σ(w_i)
    where w_i = 1 / (distance_i ^ power)

    :param target_lat: Latitude(s) of point(s) to interpolate (degrees)
    :param target_lon: Longitude(s) of point(s) to interpolate (degrees)
    :param point_lats: Latitudes for data points (degrees)
    :param point_lons: Longitudes for data points (degrees)
    :param point_values: Values at each data point
    :param power: IDW power parameter (default 2.0, higher = more local influence)
    :param search_radius: Maximum distance to consider points (meters)
    :param max_stations: Maximum number of nearest stations to use (default 12)
    :return: Interpolated value(s), None/np.nan where interpolation failed
    """
    is_batch = isinstance(target_lat, np.ndarray)

    # Validate input lengths
    if len(point_lats) != len(point_lons) or len(point_lats) != len(point_values):
        return np.full(len(target_lat), np.nan) if is_batch else None

    # Filter out None values before converting to numpy
    if isinstance(point_values, list):
        valid_data = [
            (lat, lon, val)
            for lat, lon, val in zip(point_lats, point_lons, point_values)
            if val is not None
        ]
        if not valid_data:
            return np.full(len(target_lat), np.nan) if is_batch else None
        point_lats_arr = np.array([d[0] for d in valid_data], dtype=np.float64)
        point_lons_arr = np.array([d[1] for d in valid_data], dtype=np.float64)
        point_values_arr = np.array([d[2] for d in valid_data], dtype=np.float64)
    else:
        point_lats_arr = np.asarray(point_lats, dtype=np.float64)
        point_lons_arr = np.asarray(point_lons, dtype=np.float64)
        point_values_arr = np.asarray(point_values, dtype=np.float64)
        # Filter NaN values for numpy arrays
        valid_mask = ~np.isnan(point_values_arr)
        if not np.any(valid_mask):
            return np.full(len(target_lat), np.nan) if is_batch else None
        point_lats_arr = point_lats_arr[valid_mask]
        point_lons_arr = point_lons_arr[valid_mask]
        point_values_arr = point_values_arr[valid_mask]

    if len(point_lats_arr) == 0:
        return np.full(len(target_lat), np.nan) if is_batch else None

    # For single point, wrap in array and unwrap result
    if not is_batch:
        target_lats = np.array([target_lat])
        target_lons = np.array([target_lon])
    else:
        target_lats = target_lat
        target_lons = target_lon

    # Compute distance matrix
    distances_matrix = haversine_distance(target_lats, target_lons, point_lats_arr, point_lons_arr)
    assert isinstance(distances_matrix, np.ndarray)

    n_targets = len(target_lats)
    results = np.full(n_targets, np.nan, dtype=np.float64)

    for i in range(n_targets):
        distances = distances_matrix[i]

        # Filter by search radius
        within_radius = distances <= search_radius
        valid_distances = distances[within_radius]
        valid_values = point_values_arr[within_radius]

        if len(valid_distances) == 0:
            continue

        # Check for exact match (< 1m)
        min_dist_idx = np.argmin(valid_distances)
        if valid_distances[min_dist_idx] < 1.0:
            results[i] = valid_values[min_dist_idx]
            continue

        # Sort and limit to max_stations
        if max_stations is not None and len(valid_distances) > max_stations:
            sorted_indices = np.argsort(valid_distances)[:max_stations]
            valid_distances = valid_distances[sorted_indices]
            valid_values = valid_values[sorted_indices]

        # Calculate IDW weights and weighted average
        weights = 1.0 / (valid_distances ** power)
        results[i] = np.sum(weights * valid_values) / np.sum(weights)

    # Return scalar for single point, array for batch
    if not is_batch:
        return None if np.isnan(results[0]) else float(results[0])
    return results
