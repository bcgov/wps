from datetime import datetime

import pytest
from weather_model_jobs.utils.interpolate import interpolate_bearing

time_a = datetime.fromisoformat("2020-09-03T18:00:00.000000+00:00")
time_b = datetime.fromisoformat("2020-09-03T21:00:00.000000+00:00")
target_time = datetime.fromisoformat("2020-09-03T20:00:00.000000+00:00")


@pytest.mark.parametrize(
    "direction_a,direction_b,result",
    [
        # Acute angle
        (10, 20, pytest.approx(50 / 3)),
        # Obtuse angle
        (10, 20, pytest.approx(50 / 3)),
        # Obtuse angle, interpolation in the other direction
        (200, 10, pytest.approx(940 / 3)),
        # Large obtuse angle, interpolation in the other direction
        (0, 182, pytest.approx(724 / 3)),
        # Acute angle between two bearings > 180
        (200, 220, pytest.approx(640 / 3)),
        (91, 220, 177.0),
        # Two equal angles
        (91, 91, 91.0),
        # Between two angles that extend past 360
        (300, 60, 20.0),
        # Across north, 350 to 10 (20 degrees apart)
        (350, 10, pytest.approx(10 / 3)),
        # Across north in the other direction, 10 to 350 (20 degrees apart)
        (10, 350, pytest.approx(1070 / 3)),
    ],
)
def test_interpol_b(direction_a, direction_b, result):
    assert interpolate_bearing(time_a, time_b, target_time, direction_a, direction_b) == result
