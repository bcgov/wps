from types import SimpleNamespace

import numpy as np
from geoalchemy2.elements import WKBElement
from osgeo import gdal, osr
from shapely import wkb
from shapely.geometry import Polygon

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


def test_calculate_fuel_type_areas_per_zone_clips_to_zone_geometry():
    """The whole raster is filled with fuel type 50; only a 4x4 window is overwritten with types
    1 and 2. If clip_to_geometry didn't actually restrict to the zone, type 50 would show up
    too and the areas for 1/2 would be much larger than the 8-pixel windows set below."""
    path = "/vsimem/test_fuel_type_areas_per_zone.tif"
    data = np.full((10, 10), 50, dtype=np.uint8)
    data[3:7, 3:5] = 1
    data[3:7, 5:7] = 2
    # 10x10 px, 2 units/px, covers (-10,-10)-(10,10)
    fuel_raster = WPSDataset.from_array(
        data,
        Georeference((-10, 2, 0, 10, 0, -2), osr.GetUserInputAsWKT("EPSG:3005")),
        datatype=gdal.GDT_Byte,
        output_path=path,
    )

    # Cutline (-5,-5)-(5,5) keeps only pixel centres strictly inside it, giving rows/cols 3-6 -
    # exactly the window overwritten with types 1 and 2 above.
    zone_geom = WKBElement(
        wkb.dumps(Polygon([(-5, -5), (5, -5), (5, 5), (-5, 5), (-5, -5)]), hex=True, srid=3005),
        srid=3005,
    )
    zone = SimpleNamespace(id=42, geom=zone_geom)

    result = {}
    for zone_data in calculate_fuel_type_areas_per_zone(path, [zone]):
        for advisory_shape_id, fuel_type_id, area in zone_data:
            assert advisory_shape_id == 42
            result[fuel_type_id] = area

    # pixel_size is 2, so each of the two 4x2 windows (8 pixels) covers 8 * 2 * 2 = 32.
    assert result == {1: 32, 2: 32}

    fuel_raster.close()
