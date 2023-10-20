
import math
import pytest
from app.weather_models.process_grib import calculate_wind_dir_from_u_v
from app.weather_models.wind_direction_model import compute_u_v


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
