from pathlib import Path

import numpy as np
from osgeo import gdal, osr

from fuel_grid.fuel_type_area import (
    calculate_fuel_type_area_for_zone,
    calculate_fuel_type_areas_per_zone,
)
from wps_shared.geospatial.wps_dataset import Georeference, WPSDataset


def test_calculate_fuel_type_area_for_zone():
    data = np.array([[1, 1, 2], [2, 2, 5]])

    result = dict(
        (value, area) for _, value, area in calculate_fuel_type_area_for_zone(42, data, 100)
    )

    assert result == {1: 2 * 100 * 100, 2: 3 * 100 * 100, 5: 1 * 100 * 100}


def test_calculate_fuel_type_area_for_zone_excludes_ids_outside_valid_range():
    """0 (no fuel) and 99 (non-fuel, e.g. water/urban) are not real fuel types and must be excluded."""
    data = np.array([[0, 0, 1], [99, 99, 99]])

    result = list(calculate_fuel_type_area_for_zone(42, data, 100))

    assert result == [(42, 1, 100 * 100)]


def test_calculate_fuel_type_area_for_zone_uses_advisory_shape_id():
    data = np.array([[7]])

    result = list(calculate_fuel_type_area_for_zone(123, data, 50))

    assert result == [(123, 7, 50 * 50)]


def test_calculate_fuel_type_areas_per_zone_groups_raster_values(tmp_path: Path):
    fuel_path = str(tmp_path / "fuel.tif")
    zone_path = str(tmp_path / "zones.tif")
    georeference = Georeference((-10, 2, 0, 10, 0, -2), osr.GetUserInputAsWKT("EPSG:3005"))
    fuel_raster = WPSDataset.from_array(
        np.array([[1, 99], [2, 3]], dtype=np.uint8),
        georeference,
        datatype=gdal.GDT_Byte,
        output_path=fuel_path,
    )
    zone_raster = WPSDataset.from_array(
        np.array([[1, 1], [2, -1]], dtype=np.int16),
        georeference,
        nodata_value=-1,
        datatype=gdal.GDT_Int16,
        output_path=zone_path,
    )
    fuel_raster.close()
    zone_raster.close()

    result = calculate_fuel_type_areas_per_zone(fuel_path, zone_path)

    assert result == {(1, 1): 4, (2, 2): 4}
