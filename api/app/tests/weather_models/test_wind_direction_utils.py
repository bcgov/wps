
import math
import pytest
from app.weather_models.wind_direction_utils import compute_u_v, calculate_wind_dir_from_u_v, calculate_wind_speed_from_u_v


@pytest.mark.parametrize(
    "wind_direction_deg,wind_speed",
    [
        (290, 10),
        (360, 10),
        (0, 10),
        (90, 10),
        (46.7, 10),
        (290, 23.2)
    ],
)
def test_compute_u_v(wind_direction_deg, wind_speed):
    """
    Tests computing u,v components then back again
    """
    u_v = compute_u_v(wind_speed, wind_direction_deg)
    recomputed_wind_direction = calculate_wind_dir_from_u_v(u_v[0], u_v[1])
    assert math.isclose(recomputed_wind_direction, wind_direction_deg, abs_tol=0.00001)


@pytest.mark.parametrize(
    "u_float, v_float, expected_wind_speed",
    [
        (-3.711, -1.471, 3.99),
        (2.93, 4.06, 5.01),
        (-1.77, 1.95, 2.63),
        (6.04, -0.31, 6.05),
    ],
)
def test_calculate_wind_speed_from_uv(u_float, v_float, expected_wind_speed):
    calculated_wind_speed = calculate_wind_speed_from_u_v(u_float, v_float)
    assert round(calculated_wind_speed, 2) == expected_wind_speed


@pytest.mark.parametrize(
    "u_float, v_float, expected_wind_direction",
    [
        (-3.711, -1.471, 22),
        (2.93, 4.06, 234),
        (-1.77, 1.95, 312),
        (6.04, -0.31, 177),
    ],
)
def test_calculate_wind_direction_from_uv(u_float, v_float, expected_wind_direction):
    calculated_wind_direction = calculate_wind_dir_from_u_v(u_float, v_float)
    assert round(calculated_wind_direction, 0) == expected_wind_direction
