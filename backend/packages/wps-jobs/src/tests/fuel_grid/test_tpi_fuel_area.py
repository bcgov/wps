from pathlib import Path

import numpy as np
from osgeo import gdal, osr

from wps_shared.db.models.auto_spatial_advisory import TPIClassEnum
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.geospatial.wps_dataset import Georeference
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


def test_calculate_masked_tpi_areas_groups_raster_values(tmp_path: Path):
    tpi_path = str(tmp_path / "tpi.tif")
    zone_path = str(tmp_path / "zones.tif")
    georeference = Georeference((-10, 2, 0, 10, 0, -2), osr.GetUserInputAsWKT("EPSG:3005"))
    tpi_raster = WPSDataset.from_array(
        np.array([[1, 2], [3, 4]], dtype=np.uint8),
        georeference,
        datatype=gdal.GDT_Byte,
        output_path=tpi_path,
    )
    zone_raster = WPSDataset.from_array(
        np.array([[1, 1], [2, -1]], dtype=np.int16),
        georeference,
        nodata_value=-1,
        datatype=gdal.GDT_Int16,
        output_path=zone_path,
    )
    tpi_raster.close()
    zone_raster.close()

    result = calculate_masked_tpi_areas(tpi_path, zone_path)

    assert result == {
        (1, TPIClassEnum.valley_bottom): 4,
        (1, TPIClassEnum.mid_slope): 4,
        (2, TPIClassEnum.upper_slope): 4,
    }
