import numpy as np
import pytest
from cffdrs_vec.fbp import FUEL_TYPE_CODES
from wps_shared.schemas.sfms import FuelCodesLookup

from wps_sfms.fbp_fuel_types import NODATA_FUEL_TYPE_CODE, CFFDRSFuelTypes
from wps_sfms.national_fuel_lookup import NATIONAL_FUEL_CODES, NATIONAL_FUEL_TYPES


def test_national_fuel_codes_round_trip_through_json():
    assert FuelCodesLookup.model_validate_json(NATIONAL_FUEL_CODES.model_dump_json()) == (
        NATIONAL_FUEL_CODES
    )


def test_national_fuel_codes_have_one_row_per_grid_value():
    grid_values = [row.grid_value for row in NATIONAL_FUEL_CODES.fuel_codes]
    assert len(grid_values) == len(set(grid_values))


def test_national_lookup_maps_to_cffdrs_fuel_types():
    assert NATIONAL_FUEL_TYPES.by_grid_value == {
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
    lookup = FuelCodesLookup(
        fuel_codes=[
            NATIONAL_FUEL_CODES.fuel_codes[0].model_copy(
                update={"grid_value": 60, "fuel_type": label}
            )
        ]
    )

    with pytest.raises(ValueError, match="unsupported fuel type"):
        CFFDRSFuelTypes.from_lookup(lookup)


def test_cffdrs_codes_maps_combustible_non_fuel_and_nodata_cells():
    fuel = np.array([[1, 11, 40, 101, 102, np.nan]], dtype=np.float32)

    result = NATIONAL_FUEL_TYPES.cffdrs_codes(fuel)

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
def test_cffdrs_codes_rejects_unexpected_values(fuel: np.ndarray, match: str):
    with pytest.raises(ValueError, match=match):
        NATIONAL_FUEL_TYPES.cffdrs_codes(fuel)


def test_masks_select_non_fuel_and_mixedwood_grid_values():
    fuel = np.array([[1, 40, 50, 70, 101, 102, np.nan]], dtype=np.float32)

    np.testing.assert_array_equal(
        NATIONAL_FUEL_TYPES.non_combustible_mask(fuel),
        [[False, False, False, False, True, True, False]],
    )
    np.testing.assert_array_equal(
        NATIONAL_FUEL_TYPES.mixedwood_mask(fuel), [[False, True, True, False, False, False, False]]
    )
