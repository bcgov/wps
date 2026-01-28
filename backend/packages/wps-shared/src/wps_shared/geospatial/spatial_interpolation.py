"""
Generic spatial interpolation utilities.

This module provides reusable functions for spatial interpolation of point data,
particularly useful for weather station observations (temperature, dew point, wind, etc.).
"""

import logging
from typing import List, Optional
import numpy as np
from sklearn.neighbors import RadiusNeighborsRegressor

logger = logging.getLogger(__name__)

# Earth radius in meters
EARTH_RADIUS = 6371000

# IDW parameters
IDW_POWER = 2.0  # Standard IDW power parameter
SEARCH_RADIUS = 500000  # 500km search radius in meters
MAX_STATIONS = 12  # Maximum number of nearest stations to use


def _make_idw_weights(power: float, max_stations: Optional[int]):
    """Create IDW weight function with power and max_stations parameters."""
    # Threshold for exact match: 1m in radians ≈ 1.57e-7
    exact_match_threshold = 1.0 / EARTH_RADIUS

    def weights(distances):
        # sklearn passes a list of arrays (one per query point)
        result = []
        for dist in distances:
            dist = np.asarray(dist, dtype=np.float64)
            if len(dist) == 0:
                result.append(np.array([]))
                continue

            # Check for exact match first (< 1m) - return only that weight
            min_idx = np.argmin(dist)
            if dist[min_idx] < exact_match_threshold:
                w = np.zeros(len(dist))
                w[min_idx] = 1.0
                result.append(w)
                continue

            # Limit to max_stations nearest (set others to zero weight)
            if max_stations is not None and len(dist) > max_stations:
                sorted_idx = np.argsort(dist)
                mask = np.zeros(len(dist), dtype=bool)
                mask[sorted_idx[:max_stations]] = True
            else:
                mask = np.ones(len(dist), dtype=bool)

            # IDW weights
            w = np.where(mask, 1.0 / (dist**power), 0.0)
            result.append(w)

        return result

    return weights


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
    Perform Inverse Distance Weighting (IDW) interpolation using RadiusNeighborsRegressor.

    Handles both single point and batch interpolation:
    - Scalar target_lat/lon: returns Optional[float]
    - Array target_lat/lon: returns np.ndarray of interpolated values

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

    # Convert to arrays and filter out None/NaN values
    point_lats_arr = np.asarray(point_lats, dtype=np.float64)
    point_lons_arr = np.asarray(point_lons, dtype=np.float64)
    point_values_arr = np.asarray(point_values, dtype=np.float64)
    valid_mask = ~np.isnan(point_values_arr)
    try:
        point_lats_arr = point_lats_arr[valid_mask]
        point_lons_arr = point_lons_arr[valid_mask]
        point_values_arr = point_values_arr[valid_mask]
    except IndexError:
        logger.error(
            "Input length mismatch: point_lats(%d), point_lons(%d), point_values(%d)",
            len(point_lats_arr),
            len(point_lons_arr),
            len(point_values_arr),
        )
        return np.full(len(target_lat), np.nan) if is_batch else None

    if len(point_values_arr) == 0:
        logger.error("All station values are None or NaN, cannot interpolate")
        return np.full(len(target_lat), np.nan) if is_batch else None

    # Prepare coordinates (radians for haversine)
    station_coords = np.column_stack([np.radians(point_lats_arr), np.radians(point_lons_arr)])

    # Prepare target coordinates
    if is_batch:
        target_lats, target_lons = target_lat, target_lon
    else:
        target_lats = np.array([target_lat])
        target_lons = np.array([target_lon])
    target_coords = np.column_stack([np.radians(target_lats), np.radians(target_lons)])

    # Build and fit regressor
    regressor = RadiusNeighborsRegressor(
        radius=search_radius / EARTH_RADIUS,
        weights=_make_idw_weights(power, max_stations),
        algorithm="ball_tree",
        metric="haversine",
    )
    regressor.fit(station_coords, point_values_arr)

    # Predict
    results = regressor.predict(target_coords)

    # Return scalar for single point, array for batch
    if not is_batch:
        return None if np.isnan(results[0]) else float(results[0])
    return results
