from types import SimpleNamespace

import numpy as np
from geoalchemy2.elements import WKBElement
from osgeo import gdal
from shapely import wkb
from shapely.geometry import Polygon

from wps_shared.db.models.auto_spatial_advisory import TPIClassEnum
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.tests.geospatial.dataset_common import create_test_dataset
from fuel_grid.tpi_fuel_area import calculate_masked_tpi_areas, calculate_tpi_area_data_for_zone


def test_calculate_tpi_area_data_for_zone():
    data = np.array([[1, 1, 2], [2, 2, 3]])

    result = dict(
        (tpi_class, area) for _, tpi_class, area in calculate_tpi_area_data_for_zone(42, data, 100)
    )

    assert result == {
        TPIClassEnum.valley_bottom: 2 * 100 * 100,
        TPIClassEnum.mid_slope: 3 * 100 * 100,
        TPIClassEnum.upper_slope: 1 * 100 * 100,
    }


def test_calculate_tpi_area_data_for_zone_drops_nodata_class():
    """4 is the nodata value from the TPI raster and isn't a member of TPIClassEnum, so it must be excluded."""
    data = np.array([[1, 4], [4, 4]])

    result = list(calculate_tpi_area_data_for_zone(42, data, 100))

    assert result == [(42, TPIClassEnum.valley_bottom, 100 * 100)]


def test_calculate_tpi_area_data_for_zone_uses_advisory_shape_id():
    data = np.array([[2]])

    result = list(calculate_tpi_area_data_for_zone(123, data, 50))

    assert result == [(123, TPIClassEnum.mid_slope, 50 * 50)]


def test_calculate_masked_tpi_areas_clips_to_zone_geometry(mocker):
    """The whole raster is filled with 4 (not a TPIClassEnum member, so excluded); only a 4x4
    window is overwritten with classes 1 and 2. If clip_to_geometry didn't actually restrict to
    the zone, the excluded background wouldn't matter, but the areas for 1/2 would be much
    larger than the 8-pixel windows set below."""
    extent = (-10, 10, -10, 10)  # xmin, xmax, ymin, ymax
    raw_ds = create_test_dataset(
        "masked_tpi.tif", 10, 10, extent, 3005, data_type=gdal.GDT_Byte, fill_value=4
    )
    data = np.full((10, 10), 4, dtype=np.uint8)
    data[3:7, 3:5] = 1
    data[3:7, 5:7] = 2
    raw_ds.GetRasterBand(1).WriteArray(data)

    mocker.patch(
        "fuel_grid.tpi_fuel_area.WPSDataset",
        return_value=WPSDataset(ds=raw_ds, ds_path=None),
    )

    # Cutline (-5,-5)-(5,5) keeps only pixel centres strictly inside it, giving rows/cols 3-6 -
    # exactly the window overwritten with classes 1 and 2 above.
    zone_geom = WKBElement(
        wkb.dumps(Polygon([(-5, -5), (5, -5), (5, 5), (-5, 5), (-5, -5)]), hex=True, srid=3005),
        srid=3005,
    )
    zone = SimpleNamespace(id=42, geom=zone_geom)

    result = {}
    for advisory_shape_id, tpi_class, area in calculate_masked_tpi_areas([zone], key="unused.tif"):
        assert advisory_shape_id == 42
        result[tpi_class] = area

    # pixel_size is 2, so each of the two 4x2 windows (8 pixels) covers 8 * 2 * 2 = 32.
    assert result == {TPIClassEnum.valley_bottom: 32, TPIClassEnum.mid_slope: 32}
