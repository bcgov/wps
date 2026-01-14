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


def haversine_distance_vectorized(
    target_lat: float, target_lon: float, point_lats: np.ndarray, point_lons: np.ndarray
) -> np.ndarray:
    """
    Calculate great circle distances from one point to multiple points (vectorized).

    Uses the Haversine formula with NumPy array operations for fast computation.

    :param target_lat: Latitude of target point in degrees
    :param target_lon: Longitude of target point in degrees
    :param point_lats: NumPy array of latitudes for data points (degrees)
    :param point_lons: NumPy array of longitudes for data points (degrees)
    :return: NumPy array of distances in meters
    """
    # Convert to radians
    target_lat_rad = np.radians(target_lat)
    target_lon_rad = np.radians(target_lon)
    point_lats_rad = np.radians(point_lats)
    point_lons_rad = np.radians(point_lons)

    # Haversine formula (vectorized)
    dlat = point_lats_rad - target_lat_rad
    dlon = point_lons_rad - target_lon_rad
    a = np.sin(dlat / 2) ** 2 + np.cos(target_lat_rad) * np.cos(point_lats_rad) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))

    # Earth radius in meters
    radius = 6371000
    return radius * c


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
    distances = haversine_distance_vectorized(target_lat, target_lon, lats_array, lons_array)

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
