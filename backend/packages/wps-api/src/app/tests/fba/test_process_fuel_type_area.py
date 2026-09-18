from collections import Counter

import numpy as np
from osgeo import gdal
from wps_shared.db.models.auto_spatial_advisory import SFMSFuelType
from wps_shared.geospatial.wps_dataset import WPSDataset

from app.auto_spatial_advisory.process_fuel_type_area import (
    ADVISORY_NAME,
    WARNING_NAME,
    calculate_fuel_type_areas,
    classify_by_threshold,
    count_fuel_type_hfi_pixels,
)


HFI_RASTER = np.array(
    [
        [1000, 2000, 3000, 4005],
        [5000, 10001, 11000, 12000],
        [300, 500, 7006, 9000],
        [400, 0, 1, 300],
    ]
)


def test_classify_by_thresholds_and_nan():
    assert classify_by_threshold(HFI_RASTER, 1).sum() == 4
    assert classify_by_threshold(HFI_RASTER, 2).sum() == 3
    data = np.array([[1000.0, np.nan]])
    assert classify_by_threshold(data, 1).tolist() == [[0, 0]]
    assert classify_by_threshold(data, 2).tolist() == [[0, 0]]


def test_calculate_fuel_type_areas_excludes_noncombustible_values():
    data = np.array([[1, 1, 2], [99, 0, 2]], dtype=np.uint8)
    dataset = gdal.GetDriverByName("MEM").Create("", 3, 2, 1, gdal.GDT_Byte)
    dataset.SetGeoTransform((0, 10, 0, 0, 0, -10))
    dataset.GetRasterBand(1).WriteArray(data)
    fuel_types = [
        SFMSFuelType(fuel_type_id=1, fuel_type_code="C1"),
        SFMSFuelType(fuel_type_id=2, fuel_type_code="C2"),
        SFMSFuelType(fuel_type_id=99, fuel_type_code="NF"),
    ]

    with WPSDataset(ds_path=None, ds=dataset) as source:
        assert calculate_fuel_type_areas(source, fuel_types) == {1: 200, 2: 200}


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
