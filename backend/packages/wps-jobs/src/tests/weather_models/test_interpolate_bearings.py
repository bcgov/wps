import pytest
from datetime import datetime
from weather_model_jobs.utils.interpolate import interpolate_bearing

time_a = datetime.fromisoformat("2020-09-03T18:00:00.000000+00:00")
time_b = datetime.fromisoformat("2020-09-03T21:00:00.000000+00:00")
target_time = datetime.fromisoformat("2020-09-03T20:00:00.000000+00:00")


@pytest.mark.parametrize(
    "direction_a,direction_b,result",
    [
        # Acute angle
        (10, 20, 16.666666666666668),
        # Obtuse angle
        (10, 20, 16.666666666666668),
        # Obtuse angle, interpolation in the other direction
        (200, 10, 313.3333333333333),
        # Large obtuse angle, interpolation in the other direction
        (0, 182, 241.33333333333331),
        # Acute angle between two bearings > 180
        (200, 220, 213.33333333333334),
        (91, 220, 177.0),
        # Two equal angles
        (91, 91, 91),
        # Between two angles that extend past 360
        (300, 60, 20.0),
    ],
)
def test_interpol_b(direction_a, direction_b, result):
    assert interpolate_bearing(time_a, time_b, target_time, direction_a, direction_b) == result
