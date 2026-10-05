import numpy as np
import pytest
from cffdrs_vec.fbp import FUEL_TYPE_CODES
from wps_shared.fuel_types import FuelTypeEnum

from wps_sfms.fbp_fuel_types import (
    CFFDRS_NON_FUEL_TYPES_BY_GRID_VALUE,
    FUEL_TYPES_BY_GRID_VALUE,
    GREEN_UP_GRID_VALUES,
    NATIONAL_FUEL_LOOKUP,
    NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE,
    NODATA_FUEL_TYPE_CODE,
    NON_COMBUSTIBLE_FUEL_VALUES,
    PERCENT_CONIFER_GRID_VALUES,
    fuel_type_codes_from_grid,
)


def test_bc_grid_values_translate_to_known_national_grid_values():
    known = set(FUEL_TYPES_BY_GRID_VALUE) | NON_COMBUSTIBLE_FUEL_VALUES
    assert set(NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE.values()) <= known
    assert NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE[8] == 11  # D-1
    assert NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE[12] == 31  # O-1a
    assert NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE[14] == 40  # M-1
    assert NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE[99] == 101  # Non-fuel


def test_green_up_swaps_leafless_for_green_fuel_types():
    assert {
        FUEL_TYPES_BY_GRID_VALUE[leafless]: FUEL_TYPES_BY_GRID_VALUE[green]
        for leafless, green in GREEN_UP_GRID_VALUES.items()
    } == {
        FuelTypeEnum.D1: FuelTypeEnum.D2,
        FuelTypeEnum.M1: FuelTypeEnum.M2,
        FuelTypeEnum.M3: FuelTypeEnum.M4,
    }


def test_national_lookup_covers_every_grid_value():
    assert set(NATIONAL_FUEL_LOOKUP) == set(FUEL_TYPES_BY_GRID_VALUE) | NON_COMBUSTIBLE_FUEL_VALUES


def test_non_combustible_grid_values_are_cffdrs_fuel_types():
    assert CFFDRS_NON_FUEL_TYPES_BY_GRID_VALUE == {101: "NF", 102: "WA"}
    assert -1 not in FUEL_TYPES_BY_GRID_VALUE


def test_percent_conifer_grid_values_are_derived_from_fuel_types():
    assert PERCENT_CONIFER_GRID_VALUES == frozenset({40, 50})


def test_fuel_type_codes_from_grid_maps_combustible_non_fuel_and_nodata_cells():
    fuel = np.array([[1, 11, 40, 101, 102, np.nan]], dtype=np.float32)

    result = fuel_type_codes_from_grid(fuel)

    expected = np.array(
        [
            [
                FUEL_TYPE_CODES["C1"],
                FUEL_TYPE_CODES["D1"],
                FUEL_TYPE_CODES["M1"],
                FUEL_TYPE_CODES["NF"],
                FUEL_TYPE_CODES["WA"],
                NODATA_FUEL_TYPE_CODE,
            ]
        ],
        dtype=np.int64,
    )
    np.testing.assert_array_equal(result, expected)


@pytest.mark.parametrize(
    "fuel,match",
    [
        (np.array([[-1]], dtype=np.float32), "unsupported classifications"),
        (np.array([[14]], dtype=np.float32), "unsupported classifications"),
        (np.array([[99]], dtype=np.float32), "unsupported classifications"),
        (np.array([[1.5]], dtype=np.float32), "non-integral classifications"),
    ],
)
def test_fuel_type_codes_from_grid_rejects_unexpected_values(fuel: np.ndarray, match: str):
    with pytest.raises(ValueError, match=match):
        fuel_type_codes_from_grid(fuel)
