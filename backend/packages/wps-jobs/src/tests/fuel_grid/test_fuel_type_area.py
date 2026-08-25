import numpy as np

from fuel_grid.fuel_type_area import calculate_fuel_type_area_for_zone


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
