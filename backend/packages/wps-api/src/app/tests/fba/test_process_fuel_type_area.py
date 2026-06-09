import numpy as np
from app.auto_spatial_advisory.process_fuel_type_area import (
    classify_by_threshold,
    get_fuel_type_s3_key,
)

HFI_RASTER = np.array(
    [
        [1000, 2000, 3000, 4005],
        [5000, 10001, 11000, 12000],
        [300, 500, 7006, 9000],
        [400, 0, 1, 300],
    ]
)


def test_get_warped_fuel_type_s3_key():
    bucket = "abcde"
    object_store_path = "sfms/static/fuel/2026/fbp2026_v1.tif"
    key = get_fuel_type_s3_key(bucket, object_store_path)
    assert key == f"/vsis3/{bucket}/{object_store_path}"


def test_classify_by_threshold_1():
    result = classify_by_threshold(HFI_RASTER, 1)
    # Sum array of zeros and ones, result will be a count of values from 4k - 10k.
    assert result.sum() == 4


def test_classify_by_threshold_2():
    result = classify_by_threshold(HFI_RASTER, 2)
    # Sum array of zeros and ones, result will be a count of values > 10k.
    assert result.sum() == 3
