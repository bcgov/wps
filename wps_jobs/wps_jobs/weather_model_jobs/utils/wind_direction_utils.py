import math
from typing import List, Optional


def calculate_meterological_direction(wind_dir_degrees: float):
    """
    Returns meterological wind direction from weather wind direction.
    See meterological wind direction note here: http://colaweb.gmu.edu/dev/clim301/lectures/wind/wind-uv
    """
    return 270 - wind_dir_degrees


def compute_u_v(wind_speed: float, wind_direction_degrees: int) -> Optional[List[float]]:
    if wind_speed is None or wind_direction_degrees is None:
        return None

    mdd = calculate_meterological_direction(wind_direction_degrees)
    wind_direction_radians = math.radians(mdd)

    u = wind_speed * math.sin(wind_direction_radians)
    v = wind_speed * math.cos(wind_direction_radians)
    return [u, v]


def calculate_wind_speed_from_u_v(u: float, v: float):
    """ Return calculated wind speed in metres per second from u and v components using formula
    wind_speed = sqrt(u^2 + v^2)

    What the heck is going on here?! See
    http://colaweb.gmu.edu/dev/clim301/lectures/wind/wind-uv
    """
    return math.sqrt(math.pow(u, 2) + math.pow(v, 2))


def calculate_wind_dir_from_u_v(u: float, v: float):
    """ Return calculated wind direction from u and v components using formula
    wind_direction = arctan(u, v) * 180/pi (in degrees)

    What the heck is going on here?! See
    http://colaweb.gmu.edu/dev/clim301/lectures/wind/wind-uv
    """
    calc = math.atan2(u, v) * 180 / math.pi
    # convert to meteorological convention of direction wind is coming from rather than
    # direction wind is going to
    calc += 180
    # must convert from trig coordinates to cardinal coordinates
    calc = 90 - calc
    return calc if calc > 0 else 360 + calc
