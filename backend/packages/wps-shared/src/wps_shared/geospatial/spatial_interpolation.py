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
SEARCH_RADIUS = 200000  # 200km search radius in meters


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth.

    Uses the Haversine formula to compute distance accounting for the spherical
    shape of the Earth.

    :param lat1: Latitude of first point in degrees
    :param lon1: Longitude of first point in degrees
    :param lat2: Latitude of second point in degrees
    :param lon2: Longitude of second point in degrees
    :return: Distance in meters
    """
    # Convert to radians
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
    return radius * c


def idw_interpolation(
    target_lat: float,
    target_lon: float,
    point_lats: List[float],
    point_lons: List[float],
    point_values: List[float],
    power: float = IDW_POWER,
    search_radius: float = SEARCH_RADIUS,
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

    weights = []
    values = []

    for lat, lon, value in zip(point_lats, point_lons, point_values):
        # Skip None values
        if value is None:
            continue

        # Calculate distance from target point to data point
        distance = haversine_distance(target_lat, target_lon, lat, lon)

        # Skip points outside search radius
        if distance > search_radius:
            continue

        # Handle case where point is exactly at data point location
        # Use 1 meter as threshold to avoid division by zero
        if distance < 1.0:
            logger.debug("Target point within 1m of data point, returning exact value")
            return value

        # Calculate IDW weight: inverse of distance to the power
        weight = 1.0 / (distance**power)
        weights.append(weight)
        values.append(value)

    # Check if we found any points in range
    if not weights:
        logger.debug(
            "No valid points found within search radius %.0fm of target (%.4f, %.4f)",
            search_radius,
            target_lat,
            target_lon,
        )
        return None

    # Calculate weighted average
    total_weight = sum(weights)
    interpolated_value = sum(w * v for w, v in zip(weights, values)) / total_weight

    logger.debug(
        "IDW interpolated value %.2f from %d points at (%.4f, %.4f)",
        interpolated_value,
        len(weights),
        target_lat,
        target_lon,
    )

    return interpolated_value
