"""
Checks how every cffdrs_vec.fwi/fbp vectorized_* function handles NaN and None, since they
behave very differently from each other and from the plain cffdrs scalar API:

- NaN propagates through these functions exactly like it does through the plain, unjitted cffdrs
  reference function (arithmetic NaN propagation, comparisons against NaN evaluating False) -
  numba's default "python" error model matches CPython here, so this is mostly a check that
  nothing in the jitted/cloned pipeline (eg. a fuel-type branch keyed on a NaN-derived comparison)
  quietly does something different.

- None is not accepted at all, unlike cffdrs's own scalar functions, several of which treat None
  as a "value not available" sentinel and either return None or raise a friendly CFFDRSException
  (see app.fire_behaviour.cffdrs, which wraps cffdrs for exactly this reason). numba's nopython
  mode can't type a NoneType/object array, so passing one raises immediately - a plain TypeError
  for guvectorize-based functions (rejected by numpy's own ufunc casting before numba gets
  involved, since guvectorize is eagerly compiled) or a numba.TypingError for vectorize-based ones
  (numba's own lazy compiler rejects it while inferring types for the first call). Callers must
  convert "missing" to NaN, not None, before calling into cffdrs_vec.

nan_args/none_args are already call-ready: each is the exact positional argument list `fn` is
called with (arrays, except for the trailing lat_adjust/fbp_mod bool on dc/dmc/isi, which is
passed bare - that's how it's actually broadcast against the array arguments; see
cffdrs_vec/fwi.py's callers), with one position holding NaN/None. Which position doesn't matter
(every function needs both float-only branches to still work), so each case just fixes it
wherever's convenient. call_reference takes the same nan_args list and unwraps whatever it needs
to call the plain, unjitted cffdrs function.

multi_output marks the 2 guvectorize-based functions (slope_adjustment, rate_of_spread_extended),
which return a tuple of arrays instead of one array.

Argument-array construction always happens before entering `with pytest.raises`, so those blocks
contain nothing but the single call under test - see python:S5778.
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

C6 = FUEL_TYPE_CODES["C6"]
NAN = float("nan")

# name, fn, multi_output, call_reference, nan_args, none_args
CASES = [
    # --- cffdrs_vec.fwi ---
    (
        "bui",
        fwi.vectorized_bui,
        False,
        lambda a: (cffdrs.buildup_index(float(a[0][0]), float(a[1][0])),),
        [np.array([NAN]), np.array([200.0])],
        [np.array([None]), np.array([200.0])],
    ),
    (
        "dc",
        fwi.vectorized_dc,
        False,
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
            np.array([NAN]),
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
        False,
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
            np.array([NAN]),
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
        False,
        lambda a: (
            cffdrs.fine_fuel_moisture_code(
                float(a[0][0]), float(a[1][0]), float(a[2][0]), float(a[3][0]), float(a[4][0])
            ),
        ),
        [np.array([88.0]), np.array([NAN]), np.array([40.0]), np.array([15.0]), np.array([0.0])],
        [np.array([88.0]), np.array([None]), np.array([40.0]), np.array([15.0]), np.array([0.0])],
    ),
    (
        "isi",
        fwi.vectorized_isi,
        False,
        lambda a: (cffdrs.initial_spread_index(float(a[0][0]), float(a[1][0]), a[2]),),
        [np.array([NAN]), np.array([15.0]), True],
        [np.array([None]), np.array([15.0]), True],
    ),
    (
        "fwi",
        fwi.vectorized_fwi,
        False,
        lambda a: (cffdrs.fire_weather_index(float(a[0][0]), float(a[1][0])),),
        [np.array([NAN]), np.array([40.0])],
        [np.array([None]), np.array([40.0])],
    ),
    # --- cffdrs_vec.fbp: self-contained (no fuel_type_code) ---
    (
        "critical_surface_intensity",
        fbp.vectorized_critical_surface_intensity,
        False,
        lambda a: (cffdrs.cfb_calc.critical_surface_intensity(float(a[0][0]), float(a[1][0])),),
        [np.array([NAN]), np.array([3.0])],
        [np.array([None]), np.array([3.0])],
    ),
    (
        "crown_fraction_burned",
        fbp.vectorized_crown_fraction_burned,
        False,
        lambda a: (cffdrs.cfb_calc.crown_fraction_burned(float(a[0][0]), float(a[1][0])),),
        [np.array([NAN]), np.array([1.0])],
        [np.array([None]), np.array([1.0])],
    ),
    (
        "crown_rate_of_spread_c6",
        fbp.vectorized_crown_rate_of_spread_c6,
        False,
        lambda a: (cffdrs.c6_calc.crown_rate_of_spread_c6(float(a[0][0]), float(a[1][0])),),
        [np.array([NAN]), np.array([100.0])],
        [np.array([None]), np.array([100.0])],
    ),
    (
        "intermediate_surface_rate_of_spread_c6",
        fbp.vectorized_intermediate_surface_rate_of_spread_c6,
        False,
        lambda a: (cffdrs.c6_calc.intermediate_surface_rate_of_spread_c6(float(a[0][0])),),
        [np.array([NAN])],
        [np.array([None])],
    ),
    (
        "fire_intensity",
        fbp.vectorized_fire_intensity,
        False,
        lambda a: (cffdrs.fire_intensity.fire_intensity(float(a[0][0]), float(a[1][0])),),
        [np.array([NAN]), np.array([5.0])],
        [np.array([None]), np.array([5.0])],
    ),
    (
        "foliar_moisture_content",
        fbp.vectorized_foliar_moisture_content,
        False,
        lambda a: (
            cffdrs.foliar_moisture_content.foliar_moisture_content(
                float(a[0][0]), float(a[1][0]), float(a[2][0]), float(a[3][0]), float(a[4][0])
            ),
        ),
        [np.array([NAN]), np.array([120.0]), np.array([500.0]), np.array([180.0]), np.array([0.0])],
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
        False,
        lambda a: (cffdrs.cfb_calc.surface_fire_rate_of_spread(float(a[0][0]), float(a[1][0])),),
        [np.array([NAN]), np.array([2.0])],
        [np.array([None]), np.array([2.0])],
    ),
    (
        "surface_rate_of_spread_c6",
        fbp.vectorized_surface_rate_of_spread_c6,
        False,
        lambda a: (cffdrs.c6_calc.surface_rate_of_spread_c6(float(a[0][0]), float(a[1][0])),),
        [np.array([NAN]), np.array([40.0])],
        [np.array([None]), np.array([40.0])],
    ),
    (
        "crown_fraction_burned_c6",
        fbp.vectorized_crown_fraction_burned_c6,
        False,
        lambda a: (
            cffdrs.c6_calc.crown_fraction_burned_c6(float(a[0][0]), float(a[1][0]), float(a[2][0])),
        ),
        [np.array([NAN]), np.array([4.0]), np.array([1.0])],
        [np.array([None]), np.array([4.0]), np.array([1.0])],
    ),
    # --- cffdrs_vec.fbp: fuel_type_code first, then floats ---
    (
        "distance_at_time",
        fbp.vectorized_distance_at_time,
        False,
        lambda a: (
            cffdrs.distance_at_time.distance_at_time(
                "C6", float(a[1][0]), float(a[2][0]), float(a[3][0])
            ),
        ),
        [np.array([C6]), np.array([NAN]), np.array([30.0]), np.array([0.5])],
        [np.array([C6]), np.array([None]), np.array([30.0]), np.array([0.5])],
    ),
    (
        "length_to_breadth",
        fbp.vectorized_length_to_breadth,
        False,
        lambda a: (cffdrs.length_to_breadth.length_to_breadth("C6", float(a[1][0])),),
        [np.array([C6]), np.array([NAN])],
        [np.array([C6]), np.array([None])],
    ),
    (
        "length_to_breadth_at_time",
        fbp.vectorized_length_to_breadth_at_time,
        False,
        lambda a: (
            cffdrs.length_to_breadth_at_time.length_to_breadth_at_time(
                "C6", float(a[1][0]), float(a[2][0]), float(a[3][0])
            ),
        ),
        [np.array([C6]), np.array([NAN]), np.array([30.0]), np.array([0.5])],
        [np.array([C6]), np.array([None]), np.array([30.0]), np.array([0.5])],
    ),
    (
        "rate_of_spread_at_time",
        fbp.vectorized_rate_of_spread_at_time,
        False,
        lambda a: (
            cffdrs.rate_of_spread_at_time.rate_of_spread_at_time(
                "C6", float(a[1][0]), float(a[2][0]), float(a[3][0])
            ),
        ),
        [np.array([C6]), np.array([NAN]), np.array([30.0]), np.array([0.5])],
        [np.array([C6]), np.array([None]), np.array([30.0]), np.array([0.5])],
    ),
    (
        "surface_fuel_consumption",
        fbp.vectorized_surface_fuel_consumption,
        False,
        lambda a: (
            cffdrs.surface_fuel_consumption.surface_fuel_consumption(
                "C6", float(a[1][0]), float(a[2][0]), float(a[3][0]), float(a[4][0])
            ),
        ),
        [np.array([C6]), np.array([NAN]), np.array([40.0]), np.array([50.0]), np.array([0.35])],
        [np.array([C6]), np.array([None]), np.array([40.0]), np.array([50.0]), np.array([0.35])],
    ),
    (
        "total_fuel_consumption",
        fbp.vectorized_total_fuel_consumption,
        False,
        lambda a: (
            cffdrs.total_fuel_consumption.total_fuel_consumption(
                "C6", float(a[1][0]), float(a[2][0]), float(a[3][0]), float(a[4][0]), float(a[5][0])
            ),
        ),
        [
            np.array([C6]),
            np.array([NAN]),
            np.array([0.5]),
            np.array([2.0]),
            np.array([50.0]),
            np.array([30.0]),
        ],
        [
            np.array([C6]),
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
        False,
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
            np.array([C6]),
            np.array([NAN]),
            np.array([40.0]),
            np.array([100.0]),
            np.array([2.0]),
            np.array([50.0]),
            np.array([30.0]),
            np.array([80.0]),
            np.array([3.0]),
        ],
        [
            np.array([C6]),
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
        False,
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
            np.array([C6]),
            np.array([NAN]),
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
            np.array([C6]),
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
        True,
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
            np.array([C6]),
            np.array([NAN]),
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
            np.array([C6]),
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
        True,
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
            np.array([C6]),
            np.array([NAN]),
            np.array([40.0]),
            np.array([100.0]),
            np.array([2.0]),
            np.array([50.0]),
            np.array([30.0]),
            np.array([80.0]),
            np.array([3.0]),
        ],
        [
            np.array([C6]),
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
    "name,fn,multi_output,call_reference,nan_args,none_args", CASES, ids=CASE_IDS
)
def test_nan_propagates_like_reference(name, fn, multi_output, call_reference, nan_args, none_args):
    result = fn(*nan_args)
    vec_result = tuple(field[0] for field in result) if multi_output else (result[0],)
    ref_result = call_reference(nan_args)

    np.testing.assert_allclose(vec_result, ref_result, equal_nan=True)


@pytest.mark.parametrize(
    "name,fn,multi_output,call_reference,nan_args,none_args", CASES, ids=CASE_IDS
)
def test_none_raises_clearly(name, fn, multi_output, call_reference, nan_args, none_args):
    with pytest.raises(NONE_INPUT_ERRORS):
        fn(*none_args)


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
