from datetime import date

import numpy as np
import pytest

from wps_sfms.processors.temporal_fuel import calculate_temporal_fuel, fuel_codes_lookup

# interim green-up rasters: on Jun 1 (day 152), off Sep 15 (day 258)
GREEN_UP_ON = np.full((1, 5), 152.0)
GREEN_UP_OFF = np.full((1, 5), 258.0)
# BC base values: D-1, M-1, C-3, non-fuel, nodata
BASE_FUEL = np.array([[8, 14, 3, 99, np.nan]], dtype=np.float32)


@pytest.mark.parametrize(
    "target_date,expected",
    [
        (date(2026, 5, 31), [11, 40, 3, 101, np.nan]),  # day 151, before green-up
        (date(2026, 6, 1), [12, 50, 3, 101, np.nan]),  # day 152, first green day
        (date(2026, 9, 14), [12, 50, 3, 101, np.nan]),  # day 257, last green day
        (date(2026, 9, 15), [11, 40, 3, 101, np.nan]),  # day 258, leafless again
    ],
)
def test_translates_base_fuel_and_applies_green_up(target_date: date, expected: list):
    result = calculate_temporal_fuel(BASE_FUEL, GREEN_UP_ON, GREEN_UP_OFF, target_date)

    np.testing.assert_array_equal(result, np.array([expected], dtype=np.float32))


def test_missing_julian_values_never_green_up():
    on = np.array([[np.nan, 152.0]])
    off = np.array([[258.0, np.nan]])

    result = calculate_temporal_fuel(
        np.array([[8, 8]], dtype=np.float32), on, off, date(2026, 7, 1)
    )

    np.testing.assert_array_equal(result, np.array([[11, 11]], dtype=np.float32))


@pytest.mark.parametrize("value", [0, 15, 101, 1.5])
def test_rejects_unsupported_base_fuel_values(value: float):
    with pytest.raises(ValueError, match="unsupported classifications"):
        calculate_temporal_fuel(
            np.array([[value]], dtype=np.float32),
            GREEN_UP_ON[:, :1],
            GREEN_UP_OFF[:, :1],
            date(2026, 7, 1),
        )


def test_fuel_codes_lookup_lists_present_grid_values_in_order():
    temporal = np.array([[50, 12, 101, 12, np.nan]], dtype=np.float32)

    result = fuel_codes_lookup(temporal)

    assert [row.grid_value for row in result.root] == [12, 50, 101]
    assert result.root[0].model_dump() == {
        "grid_value": 12,
        "export_value": 12,
        "descriptive_name": "Green Aspen (with BUI Thresholding)",
        "fuel_type": "D-2",
        "r": 137,
        "g": 112,
        "b": 68,
        "h": 27,
        "s": 86,
        "l": 103,
    }
