from collections import Counter

import numpy as np

from app.auto_spatial_advisory.process_fuel_type_area import (
    ADVISORY_NAME,
    WARNING_NAME,
    count_fuel_type_hfi_pixels,
)


def test_count_fuel_type_hfi_pixels_groups_by_zone_and_threshold():
    counts = Counter()

    count_fuel_type_hfi_pixels(
        counts,
        zones=np.array([[1, 1, 2], [1, 2, -1]]),
        raw_hfi=np.array([[5000, 11000, 9000], [3000, 12000, 12000]]),
        fuel_types=np.array([[2, 3, 2], [4, 99, 5]]),
        zone_nodata=-1,
    )

    assert counts == Counter(
        {
            (1, ADVISORY_NAME, 2): 1,
            (1, WARNING_NAME, 3): 1,
            (2, ADVISORY_NAME, 2): 1,
        }
    )


def test_count_fuel_type_hfi_pixels_handles_threshold_boundaries_and_invalid_pixels():
    counts = Counter()

    count_fuel_type_hfi_pixels(
        counts,
        zones=np.ones((1, 8), dtype=np.int16),
        raw_hfi=np.array([[3999, 4000, 9999, 10000, np.nan, 5000, 11000, 12000]]),
        fuel_types=np.array([[2, 2, 2, 2, 2, 0, 99, 100]]),
        zone_nodata=-1,
    )

    assert counts == {(1, ADVISORY_NAME, 2): 2, (1, WARNING_NAME, 2): 1}
