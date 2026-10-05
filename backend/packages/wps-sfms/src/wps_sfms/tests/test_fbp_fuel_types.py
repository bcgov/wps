import numpy as np
import pytest
from cffdrs_vec.fbp import FUEL_TYPE_CODES
from wps_shared.schemas.sfms import FuelCodesLookup

from wps_sfms.fbp_fuel_types import (
    GREEN_UP_GRID_VALUES,
    NATIONAL_FUEL_LOOKUP,
    NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE,
    NODATA_FUEL_TYPE_CODE,
    cffdrs_fuel_types_from_lookup,
    fuel_type_codes_from_grid,
)

FUEL_CODES_LOOKUP = FuelCodesLookup(list(NATIONAL_FUEL_LOOKUP.values()))
FUEL_TYPES = cffdrs_fuel_types_from_lookup(FUEL_CODES_LOOKUP)


def test_fuel_codes_lookup_round_trips_through_json():
    assert FuelCodesLookup.model_validate_json(FUEL_CODES_LOOKUP.model_dump_json()) == (
        FUEL_CODES_LOOKUP
    )


def test_national_lookup_maps_to_cffdrs_fuel_types():
    assert FUEL_TYPES == {
        1: "C1",
        2: "C2",
        3: "C3",
        4: "C4",
        5: "C5",
        6: "C6",
        7: "C7",
        11: "D1",
        12: "D2",
        21: "S1",
        22: "S2",
        23: "S3",
        31: "O1A",
        32: "O1B",
        40: "M1",
        50: "M2",
        70: "M3",
        80: "M4",
        101: "NF",
        102: "NF",
    }


@pytest.mark.parametrize("label", ["M-1/M-2", "M-1 (05 PC)", "Unknown"])
def test_lookup_rejects_fuel_types_cffdrs_cannot_calculate(label: str):
    with pytest.raises(ValueError, match="unsupported fuel type"):
        cffdrs_fuel_types_from_lookup(
            FuelCodesLookup(
                [NATIONAL_FUEL_LOOKUP[40].model_copy(update={"grid_value": 60, "fuel_type": label})]
            )
        )


def test_bc_grid_values_translate_to_national_lookup_values():
    assert set(NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE.values()) <= set(NATIONAL_FUEL_LOOKUP)
    assert NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE[8] == 11  # D-1
    assert NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE[12] == 31  # O-1a
    assert NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE[14] == 40  # M-1
    assert NATIONAL_GRID_VALUES_BY_BC_GRID_VALUE[99] == 101  # Non-fuel


def test_green_up_swaps_leafless_for_green_fuel_types():
    assert {
        FUEL_TYPES[leafless]: FUEL_TYPES[green] for leafless, green in GREEN_UP_GRID_VALUES.items()
    } == {"D1": "D2", "M1": "M2", "M3": "M4"}


def test_fuel_type_codes_from_grid_maps_combustible_non_fuel_and_nodata_cells():
    fuel = np.array([[1, 11, 40, 101, 102, np.nan]], dtype=np.float32)

    result = fuel_type_codes_from_grid(fuel, FUEL_TYPES)

    expected = np.array(
        [
            [
                FUEL_TYPE_CODES["C1"],
                FUEL_TYPE_CODES["D1"],
                FUEL_TYPE_CODES["M1"],
                FUEL_TYPE_CODES["NF"],
                FUEL_TYPE_CODES["NF"],
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
        fuel_type_codes_from_grid(fuel, FUEL_TYPES)
