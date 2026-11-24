"""Wind as a speed and the direction it blows from, and as the u and v components that models
publish: u towards the east and v towards the north."""

import math
from typing import List, Optional


def compute_u_v(wind_speed: float, wind_direction_degrees: float) -> Optional[List[float]]:
    """The u and v components of a wind from its speed and the direction it blows from."""
    if wind_speed is None or wind_direction_degrees is None:
        return None

    radians = math.radians(wind_direction_degrees)
    return [-wind_speed * math.sin(radians), -wind_speed * math.cos(radians)]


def calculate_wind_speed_from_u_v(u: float, v: float):
    """Wind speed from its u and v components, in their units."""
    return math.sqrt(math.pow(u, 2) + math.pow(v, 2))


def calculate_wind_dir_from_u_v(u: float, v: float) -> float:
    """The direction a wind blows from, in degrees clockwise from north, from its u and v
    components. North is 360, not 0."""
    return math.degrees(math.atan2(-u, -v)) % 360 or 360.0
