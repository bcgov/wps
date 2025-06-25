from wps_shared import config
from app.auto_spatial_advisory.process_fuel_type_area import get_fuel_type_s3_key, classify_by_threshold
import numpy as np


HFI_RASTER = np.array([[1000, 2000, 3000, 4005], [5000, 10001, 11000, 12000], [300, 500, 7006, 9000], [400, 0, 1, 300]])

mock_fuel_raster_name = "fbp2024.tif"


def get_mock_fuel_raster_name():
    return mock_fuel_raster_name

def test_get_warped_fuel_type_s3_key():
    bucket = "abcde"
    key = get_fuel_type_s3_key(bucket)
    fuel_raster_name = config.get("FUEL_RASTER_NAME")
    assert key == f"/vsis3/{bucket}/sfms/static/{fuel_raster_name}"
    

def test_classify_by_threshold_1():
    result = classify_by_threshold(HFI_RASTER, 1)
    # Sum array of zeros and ones, result will be a count of values from 4k - 10k.
    assert result.sum() == 4


def test_classify_by_threshold_2():
    result = classify_by_threshold(HFI_RASTER, 2)
    # Sum array of zeros and ones, result will be a count of values > 10k.
    assert result.sum() == 3
