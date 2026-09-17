from collections import Counter

import numpy as np

from app.auto_spatial_advisory.process_high_hfi_area import count_high_hfi_pixels


def test_count_high_hfi_pixels_groups_classes_by_zone():
    counts = Counter()

    count_high_hfi_pixels(
        counts,
        zones=np.array([[1, 1, 2], [1, 2, -1]]),
        hfi=np.array([[1, 2, 1], [0, 0, 2]]),
        zone_nodata=-1,
    )

    assert counts == Counter({(1, 1): 1, (1, 2): 1, (2, 1): 1})
