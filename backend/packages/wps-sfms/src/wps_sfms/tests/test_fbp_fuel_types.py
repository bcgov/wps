import numpy as np
import pytest
from cffdrs_vec.fbp import FUEL_TYPE_CODES
from wps_shared.fuel_types import FuelTypeEnum

from wps_sfms.fbp_fuel_types import (
    FUEL_TYPES_BY_GRID_VALUE,
    NO_FUEL_TYPE_CODE,
    NON_COMBUSTIBLE_FUEL_VALUES,
    PERCENT_CONIFER_GRID_VALUES,
    SEASONAL_FUEL_TYPE_OVERRIDES,
    fuel_type_codes_from_grid,
)


def test_base_fuel_types_cover_combustible_grid_values():
    assert FUEL_TYPES_BY_GRID_VALUE == {
        1: FuelTypeEnum.C1,
        2: FuelTypeEnum.C2,
        3: FuelTypeEnum.C3,
        4: FuelTypeEnum.C4,
        5: FuelTypeEnum.C5,
        6: FuelTypeEnum.C6,
        7: FuelTypeEnum.C7,
        8: FuelTypeEnum.D1,
        9: FuelTypeEnum.S1,
        10: FuelTypeEnum.S2,
        11: FuelTypeEnum.S3,
        12: FuelTypeEnum.O1A,
        13: FuelTypeEnum.M3,
        14: FuelTypeEnum.M1,
    }


def test_seasonal_fuel_type_overrides_cover_combined_grid_values():
    assert SEASONAL_FUEL_TYPE_OVERRIDES == {
        8: FuelTypeEnum.D2,
        12: FuelTypeEnum.O1B,
        13: FuelTypeEnum.M4,
        14: FuelTypeEnum.M2,
    }


def test_non_combustible_and_unsupported_xml_values():
    assert NON_COMBUSTIBLE_FUEL_VALUES == frozenset({99, 100, 102})
    assert -1 not in FUEL_TYPES_BY_GRID_VALUE


def test_percent_conifer_grid_values_are_derived_from_base_fuel_types():
    assert PERCENT_CONIFER_GRID_VALUES == frozenset({14})


def test_fuel_type_codes_from_grid_maps_combustible_and_ignored_cells():
    fuel = np.array([[1, 8, 14, 99, 100, 102, np.nan]], dtype=np.float32)

    result = fuel_type_codes_from_grid(fuel)

    expected = np.array(
        [
            [
                FUEL_TYPE_CODES["C1"],
                FUEL_TYPE_CODES["D1"],
                FUEL_TYPE_CODES["M1"],
                NO_FUEL_TYPE_CODE,
                NO_FUEL_TYPE_CODE,
                NO_FUEL_TYPE_CODE,
                NO_FUEL_TYPE_CODE,
            ]
        ],
        dtype=np.int64,
    )
    np.testing.assert_array_equal(result, expected)


@pytest.mark.parametrize(
    "fuel,match",
    [
        (np.array([[-1]], dtype=np.float32), "unsupported classifications"),
        (np.array([[15]], dtype=np.float32), "unsupported classifications"),
        (np.array([[1.5]], dtype=np.float32), "non-integral classifications"),
    ],
)
def test_fuel_type_codes_from_grid_rejects_unexpected_values(fuel: np.ndarray, match: str):
    with pytest.raises(ValueError, match=match):
        fuel_type_codes_from_grid(fuel)
