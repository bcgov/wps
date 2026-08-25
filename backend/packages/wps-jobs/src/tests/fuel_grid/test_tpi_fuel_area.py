import numpy as np

from wps_shared.db.models.auto_spatial_advisory import TPIClassEnum
from fuel_grid.tpi_fuel_area import calculate_tpi_area_data_for_zone


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
