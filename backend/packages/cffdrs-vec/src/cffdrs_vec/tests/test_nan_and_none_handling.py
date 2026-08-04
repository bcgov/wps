"""
Checks how every cffdrs_vec.fwi/fbp vectorized_* function handles NaN and None:

- NaN propagates through these functions exactly like it does through the plain, unjitted cffdrs
  reference function (arithmetic NaN propagation, comparisons against NaN evaluating False).
- None is never accepted: numba's nopython mode can't type a NoneType/object array, so passing
  one raises immediately (see NONE_INPUT_ERRORS below for which exception type, depending on
  function). This differs from cffdrs's own scalar functions, several of which treat None as a
  "value not available" sentinel (see app.fire_behaviour.cffdrs, which wraps cffdrs for exactly
  that reason). Callers must convert "missing" to NaN, not None, before calling into cffdrs_vec.
"""

import cffdrs
import cffdrs.back_rate_of_spread
import cffdrs.c6_calc
import cffdrs.cfb_calc
import cffdrs.distance_at_time
import cffdrs.fire_intensity
import cffdrs.foliar_moisture_content
import cffdrs.length_to_breadth
import cffdrs.length_to_breadth_at_time
import cffdrs.rate_of_spread
import cffdrs.rate_of_spread_at_time
import cffdrs.slope_calc
import cffdrs.surface_fuel_consumption
import cffdrs.total_fuel_consumption
import numba
import numpy as np
import pytest
from cffdrs.constants import FUEL_TYPE_CODES

from cffdrs_vec import fbp, fwi

# vectorize-based functions raise numba's own TypingError (lazy compilation rejects a None/object
# array while inferring types); guvectorize-based ones are eagerly compiled, so numpy's ufunc
# casting rejects a None/object array with a plain TypeError before numba is even involved.
NONE_INPUT_ERRORS = (TypeError, numba.TypingError)

# Each case is (fn_name, vectorized_fn, reference_fn, nan_args, none_args):
# - vectorized_fn is the cffdrs_vec function under test.
# - nan_args/none_args are vectorized_fn's exact positional argument list. Every argument is a
#   1-element array, EXCEPT the trailing lat_adjust/fbp_mod bool that dc/dmc/isi take, which is a
#   bare Python bool instead - that matches how production code actually calls them (see
#   fwi_processor.py's vectorized_dc/dmc/isi calls): numpy broadcasts a bare scalar against array
#   arguments fine, so real callers never bother wrapping it in an array either.
# - Exactly one argument position holds NaN (or None) instead of its normal value. Which position
#   is arbitrary, the test just needs some float argument to be missing, not a specific one, so
#   each case picks whichever's convenient to write.
# - reference_fn takes nan_args and unwraps whatever it needs to call the plain, unjitted cffdrs
#   function, as the oracle vectorized_fn's result gets checked against.
# `vectorized_fn.nout` (numba's vectorize/guvectorize wrappers are ufunc-like) tells the tests
# below whether `vectorized_fn(*args)` returns one array or a tuple of arrays -
# slope_adjustment/rate_of_spread_extended are the only 2 guvectorize-based cases, with nout 2
# and 4 respectively.
CASES = [
    # --- cffdrs_vec.fwi ---
    (
        "bui",
        fwi.vectorized_bui,
        lambda a: (cffdrs.buildup_index(float(a[0][0]), float(a[1][0])),),
        [np.array([np.nan]), np.array([200.0])],
        [np.array([None]), np.array([200.0])],
    ),
    (
        "dc",
        fwi.vectorized_dc,
        lambda a: (
            cffdrs.drought_code(
                float(a[0][0]),
                float(a[1][0]),
                float(a[2][0]),
                float(a[3][0]),
                float(a[4][0]),
                int(a[5][0]),
                a[6],
            ),
        ),
        [
            np.array([200.0]),
            np.array([np.nan]),
            np.array([40.0]),
            np.array([0.0]),
            np.array([55.0]),
            np.array([7]),
            True,
        ],
        [
            np.array([200.0]),
            np.array([None]),
            np.array([40.0]),
            np.array([0.0]),
            np.array([55.0]),
            np.array([7]),
            True,
        ],
    ),
    (
        "dmc",
        fwi.vectorized_dmc,
        lambda a: (
            cffdrs.duff_moisture_code(
                float(a[0][0]),
                float(a[1][0]),
                float(a[2][0]),
                float(a[3][0]),
                float(a[4][0]),
                int(a[5][0]),
                a[6],
            ),
        ),
        [
            np.array([50.0]),
            np.array([np.nan]),
            np.array([40.0]),
            np.array([0.0]),
            np.array([55.0]),
            np.array([7]),
            True,
        ],
        [
            np.array([50.0]),
            np.array([None]),
            np.array([40.0]),
            np.array([0.0]),
            np.array([55.0]),
            np.array([7]),
            True,
        ],
    ),
    (
        "ffmc",
        fwi.vectorized_ffmc,
        lambda a: (
            cffdrs.fine_fuel_moisture_code(
                float(a[0][0]), float(a[1][0]), float(a[2][0]), float(a[3][0]), float(a[4][0])
            ),
        ),
        [np.array([88.0]), np.array([np.nan]), np.array([40.0]), np.array([15.0]), np.array([0.0])],
        [np.array([88.0]), np.array([None]), np.array([40.0]), np.array([15.0]), np.array([0.0])],
    ),
    (
        "isi",
        fwi.vectorized_isi,
        lambda a: (cffdrs.initial_spread_index(float(a[0][0]), float(a[1][0]), a[2]),),
        [np.array([np.nan]), np.array([15.0]), True],
        [np.array([None]), np.array([15.0]), True],
    ),
    (
        "fwi",
        fwi.vectorized_fwi,
        lambda a: (cffdrs.fire_weather_index(float(a[0][0]), float(a[1][0])),),
        [np.array([np.nan]), np.array([40.0])],
        [np.array([None]), np.array([40.0])],
    ),
    # --- cffdrs_vec.fbp: self-contained (no fuel_type_code) ---
    (
        "critical_surface_intensity",
        fbp.vectorized_critical_surface_intensity,
        lambda a: (cffdrs.cfb_calc.critical_surface_intensity(float(a[0][0]), float(a[1][0])),),
        [np.array([np.nan]), np.array([3.0])],
        [np.array([None]), np.array([3.0])],
    ),
    (
        "crown_fraction_burned",
        fbp.vectorized_crown_fraction_burned,
        lambda a: (cffdrs.cfb_calc.crown_fraction_burned(float(a[0][0]), float(a[1][0])),),
        [np.array([np.nan]), np.array([1.0])],
        [np.array([None]), np.array([1.0])],
    ),
    (
        "crown_rate_of_spread_c6",
        fbp.vectorized_crown_rate_of_spread_c6,
        lambda a: (cffdrs.c6_calc.crown_rate_of_spread_c6(float(a[0][0]), float(a[1][0])),),
        [np.array([np.nan]), np.array([100.0])],
        [np.array([None]), np.array([100.0])],
    ),
    (
        "intermediate_surface_rate_of_spread_c6",
        fbp.vectorized_intermediate_surface_rate_of_spread_c6,
        lambda a: (cffdrs.c6_calc.intermediate_surface_rate_of_spread_c6(float(a[0][0])),),
        [np.array([np.nan])],
        [np.array([None])],
    ),
    (
        "fire_intensity",
        fbp.vectorized_fire_intensity,
        lambda a: (cffdrs.fire_intensity.fire_intensity(float(a[0][0]), float(a[1][0])),),
        [np.array([np.nan]), np.array([5.0])],
        [np.array([None]), np.array([5.0])],
    ),
    (
        "foliar_moisture_content",
        fbp.vectorized_foliar_moisture_content,
        lambda a: (
            cffdrs.foliar_moisture_content.foliar_moisture_content(
                float(a[0][0]), float(a[1][0]), float(a[2][0]), float(a[3][0]), float(a[4][0])
            ),
        ),
        [
            np.array([np.nan]),
            np.array([120.0]),
            np.array([500.0]),
            np.array([180.0]),
            np.array([0.0]),
        ],
        [
            np.array([None]),
            np.array([120.0]),
            np.array([500.0]),
            np.array([180.0]),
            np.array([0.0]),
        ],
    ),
    (
        "surface_fire_rate_of_spread",
        fbp.vectorized_surface_fire_rate_of_spread,
        lambda a: (cffdrs.cfb_calc.surface_fire_rate_of_spread(float(a[0][0]), float(a[1][0])),),
        [np.array([np.nan]), np.array([2.0])],
        [np.array([None]), np.array([2.0])],
    ),
    (
        "surface_rate_of_spread_c6",
        fbp.vectorized_surface_rate_of_spread_c6,
        lambda a: (cffdrs.c6_calc.surface_rate_of_spread_c6(float(a[0][0]), float(a[1][0])),),
        [np.array([np.nan]), np.array([40.0])],
        [np.array([None]), np.array([40.0])],
    ),
    (
        "crown_fraction_burned_c6",
        fbp.vectorized_crown_fraction_burned_c6,
        lambda a: (
            cffdrs.c6_calc.crown_fraction_burned_c6(float(a[0][0]), float(a[1][0]), float(a[2][0])),
        ),
        [np.array([np.nan]), np.array([4.0]), np.array([1.0])],
        [np.array([None]), np.array([4.0]), np.array([1.0])],
    ),
    # --- cffdrs_vec.fbp: fuel_type_code first, then floats ---
    (
        "distance_at_time",
        fbp.vectorized_distance_at_time,
        lambda a: (
            cffdrs.distance_at_time.distance_at_time(
                "C6", float(a[1][0]), float(a[2][0]), float(a[3][0])
            ),
        ),
        [np.array([FUEL_TYPE_CODES["C6"]]), np.array([np.nan]), np.array([30.0]), np.array([0.5])],
        [np.array([FUEL_TYPE_CODES["C6"]]), np.array([None]), np.array([30.0]), np.array([0.5])],
    ),
    (
        "length_to_breadth",
        fbp.vectorized_length_to_breadth,
        lambda a: (cffdrs.length_to_breadth.length_to_breadth("C6", float(a[1][0])),),
        [np.array([FUEL_TYPE_CODES["C6"]]), np.array([np.nan])],
        [np.array([FUEL_TYPE_CODES["C6"]]), np.array([None])],
    ),
    (
        "length_to_breadth_at_time",
        fbp.vectorized_length_to_breadth_at_time,
        lambda a: (
            cffdrs.length_to_breadth_at_time.length_to_breadth_at_time(
                "C6", float(a[1][0]), float(a[2][0]), float(a[3][0])
            ),
        ),
        [np.array([FUEL_TYPE_CODES["C6"]]), np.array([np.nan]), np.array([30.0]), np.array([0.5])],
        [np.array([FUEL_TYPE_CODES["C6"]]), np.array([None]), np.array([30.0]), np.array([0.5])],
    ),
    (
        "rate_of_spread_at_time",
        fbp.vectorized_rate_of_spread_at_time,
        lambda a: (
            cffdrs.rate_of_spread_at_time.rate_of_spread_at_time(
                "C6", float(a[1][0]), float(a[2][0]), float(a[3][0])
            ),
        ),
        [np.array([FUEL_TYPE_CODES["C6"]]), np.array([np.nan]), np.array([30.0]), np.array([0.5])],
        [np.array([FUEL_TYPE_CODES["C6"]]), np.array([None]), np.array([30.0]), np.array([0.5])],
    ),
    (
        "surface_fuel_consumption",
        fbp.vectorized_surface_fuel_consumption,
        lambda a: (
            cffdrs.surface_fuel_consumption.surface_fuel_consumption(
                "C6", float(a[1][0]), float(a[2][0]), float(a[3][0]), float(a[4][0])
            ),
        ),
        [
            np.array([FUEL_TYPE_CODES["C6"]]),
            np.array([np.nan]),
            np.array([40.0]),
            np.array([50.0]),
            np.array([0.35]),
        ],
        [
            np.array([FUEL_TYPE_CODES["C6"]]),
            np.array([None]),
            np.array([40.0]),
            np.array([50.0]),
            np.array([0.35]),
        ],
    ),
    (
        "total_fuel_consumption",
        fbp.vectorized_total_fuel_consumption,
        lambda a: (
            cffdrs.total_fuel_consumption.total_fuel_consumption(
                "C6", float(a[1][0]), float(a[2][0]), float(a[3][0]), float(a[4][0]), float(a[5][0])
            ),
        ),
        [
            np.array([FUEL_TYPE_CODES["C6"]]),
            np.array([np.nan]),
            np.array([0.5]),
            np.array([2.0]),
            np.array([50.0]),
            np.array([30.0]),
        ],
        [
            np.array([FUEL_TYPE_CODES["C6"]]),
            np.array([None]),
            np.array([0.5]),
            np.array([2.0]),
            np.array([50.0]),
            np.array([30.0]),
        ],
    ),
    (
        "rate_of_spread",
        fbp.vectorized_rate_of_spread,
        lambda a: (
            cffdrs.rate_of_spread.rate_of_spread(
                "C6",
                float(a[1][0]),
                float(a[2][0]),
                float(a[3][0]),
                float(a[4][0]),
                float(a[5][0]),
                float(a[6][0]),
                float(a[7][0]),
                float(a[8][0]),
            ),
        ),
        [
            np.array([FUEL_TYPE_CODES["C6"]]),
            np.array([np.nan]),
            np.array([40.0]),
            np.array([100.0]),
            np.array([2.0]),
            np.array([50.0]),
            np.array([30.0]),
            np.array([80.0]),
            np.array([3.0]),
        ],
        [
            np.array([FUEL_TYPE_CODES["C6"]]),
            np.array([None]),
            np.array([40.0]),
            np.array([100.0]),
            np.array([2.0]),
            np.array([50.0]),
            np.array([30.0]),
            np.array([80.0]),
            np.array([3.0]),
        ],
    ),
    (
        "back_rate_of_spread",
        fbp.vectorized_back_rate_of_spread,
        lambda a: (
            cffdrs.back_rate_of_spread.back_rate_of_spread(
                "C6",
                float(a[1][0]),
                float(a[2][0]),
                float(a[3][0]),
                float(a[4][0]),
                float(a[5][0]),
                float(a[6][0]),
                float(a[7][0]),
                float(a[8][0]),
                float(a[9][0]),
            ),
        ),
        [
            np.array([FUEL_TYPE_CODES["C6"]]),
            np.array([np.nan]),
            np.array([40.0]),
            np.array([15.0]),
            np.array([100.0]),
            np.array([2.0]),
            np.array([50.0]),
            np.array([30.0]),
            np.array([80.0]),
            np.array([3.0]),
        ],
        [
            np.array([FUEL_TYPE_CODES["C6"]]),
            np.array([None]),
            np.array([40.0]),
            np.array([15.0]),
            np.array([100.0]),
            np.array([2.0]),
            np.array([50.0]),
            np.array([30.0]),
            np.array([80.0]),
            np.array([3.0]),
        ],
    ),
    # --- cffdrs_vec.fbp: multi-output (guvectorize) ---
    (
        "slope_adjustment",
        fbp.vectorized_slope_adjustment,
        lambda a: (lambda r: (r.wsv, r.raz))(
            cffdrs.slope_calc.slope_adjustment(
                "C6",
                float(a[1][0]),
                float(a[2][0]),
                float(a[3][0]),
                float(a[4][0]),
                float(a[5][0]),
                float(a[6][0]),
                float(a[7][0]),
                float(a[8][0]),
                float(a[9][0]),
                float(a[10][0]),
                float(a[11][0]),
                float(a[12][0]),
                float(a[13][0]),
            )
        ),
        [
            np.array([FUEL_TYPE_CODES["C6"]]),
            np.array([np.nan]),
            np.array([40.0]),
            np.array([15.0]),
            np.array([1.2]),
            np.array([20.0]),
            np.array([0.5]),
            np.array([100.0]),
            np.array([2.0]),
            np.array([50.0]),
            np.array([30.0]),
            np.array([80.0]),
            np.array([3.0]),
            np.array([10.0]),
        ],
        [
            np.array([FUEL_TYPE_CODES["C6"]]),
            np.array([None]),
            np.array([40.0]),
            np.array([15.0]),
            np.array([1.2]),
            np.array([20.0]),
            np.array([0.5]),
            np.array([100.0]),
            np.array([2.0]),
            np.array([50.0]),
            np.array([30.0]),
            np.array([80.0]),
            np.array([3.0]),
            np.array([10.0]),
        ],
    ),
    (
        "rate_of_spread_extended",
        fbp.vectorized_rate_of_spread_extended,
        lambda a: (lambda r: (r.ros, r.cfb, r.csi, r.rso))(
            cffdrs.rate_of_spread.rate_of_spread_extended(
                "C6",
                float(a[1][0]),
                float(a[2][0]),
                float(a[3][0]),
                float(a[4][0]),
                float(a[5][0]),
                float(a[6][0]),
                float(a[7][0]),
                float(a[8][0]),
            )
        ),
        [
            np.array([FUEL_TYPE_CODES["C6"]]),
            np.array([np.nan]),
            np.array([40.0]),
            np.array([100.0]),
            np.array([2.0]),
            np.array([50.0]),
            np.array([30.0]),
            np.array([80.0]),
            np.array([3.0]),
        ],
        [
            np.array([FUEL_TYPE_CODES["C6"]]),
            np.array([None]),
            np.array([40.0]),
            np.array([100.0]),
            np.array([2.0]),
            np.array([50.0]),
            np.array([30.0]),
            np.array([80.0]),
            np.array([3.0]),
        ],
    ),
]

CASE_IDS = [case[0] for case in CASES]


@pytest.mark.parametrize(
    "fn_name,vectorized_fn,reference_fn,nan_args,none_args", CASES, ids=CASE_IDS
)
def test_nan_propagates_like_reference(fn_name, vectorized_fn, reference_fn, nan_args, none_args):
    result = vectorized_fn(*nan_args)
    vec_result = tuple(field[0] for field in result) if vectorized_fn.nout > 1 else (result[0],)
    ref_result = reference_fn(nan_args)

    np.testing.assert_allclose(vec_result, ref_result, equal_nan=True)


@pytest.mark.parametrize(
    "fn_name,vectorized_fn,reference_fn,nan_args,none_args", CASES, ids=CASE_IDS
)
def test_none_raises_clearly(fn_name, vectorized_fn, reference_fn, nan_args, none_args):
    with pytest.raises(NONE_INPUT_ERRORS):
        vectorized_fn(*none_args)


def test_none_fuel_type_code_raises_clearly_vectorize_based():
    """fuel_type_code itself is also rejected as None, not just the float positions above -
    checked once each for a vectorize-based and a guvectorize-based function, since that's
    the mechanism that actually determines which exception type is raised (see module docstring).

    The args are built here, not inline in the `with` block, so that block contains only the one
    call under test - see python:S5778.
    """
    args = [
        np.array([None]),
        np.array([10.0]),
        np.array([40.0]),
        np.array([100.0]),
        np.array([2.0]),
        np.array([50.0]),
        np.array([30.0]),
        np.array([80.0]),
        np.array([3.0]),
    ]
    with pytest.raises(NONE_INPUT_ERRORS):
        fbp.vectorized_rate_of_spread(*args)


def test_none_fuel_type_code_raises_clearly_guvectorize_based():
    args = [
        np.array([None]),
        np.array([10.0]),
        np.array([40.0]),
        np.array([100.0]),
        np.array([2.0]),
        np.array([50.0]),
        np.array([30.0]),
        np.array([80.0]),
        np.array([3.0]),
    ]
    with pytest.raises(NONE_INPUT_ERRORS):
        fbp.vectorized_rate_of_spread_extended(*args)
