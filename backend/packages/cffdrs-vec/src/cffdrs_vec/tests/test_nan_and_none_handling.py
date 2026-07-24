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

Each FunctionSpec's `prepare` builds ready-to-call arguments (arrays, or bare bools for the
trailing lat_adjust/fbp_mod flags) before any exception is expected, so the `with pytest.raises`
blocks below contain nothing but the single call under test - see python:S5778.
"""

from collections import namedtuple

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

C1 = FUEL_TYPE_CODES["C1"]
C6 = FUEL_TYPE_CODES["C6"]

FunctionSpec = namedtuple(
    "FunctionSpec", ["id", "fn", "prepare", "extract", "call_reference", "args", "swap_index"]
)


def _wrap_all(args):
    """Wrap every argument as a 1-element array - the default calling convention."""
    return [np.array([value]) for value in args]


def _wrap_all_but_last(args):
    """Same as _wrap_all, but the trailing lat_adjust/fbp_mod flag stays a bare bool - that's how
    it's actually broadcast against the array arguments (see cffdrs_vec/fwi.py's callers).
    """
    return [np.array([value]) for value in args[:-1]] + [args[-1]]


def _extract_single(result):
    return (result[0],)


def _extract_multi(result):
    return tuple(field[0] for field in result)


SPECS = [
    # --- cffdrs_vec.fwi ---
    FunctionSpec(
        "bui",
        fwi.vectorized_bui,
        _wrap_all,
        _extract_single,
        lambda a: (cffdrs.buildup_index(a[0], a[1]),),
        [100.0, 200.0],
        0,
    ),
    FunctionSpec(
        "dc",
        fwi.vectorized_dc,
        _wrap_all_but_last,
        _extract_single,
        lambda a: (cffdrs.drought_code(a[0], a[1], a[2], a[3], a[4], a[5], a[6]),),
        [200.0, 20.0, 40.0, 0.0, 55.0, 7, True],
        1,
    ),
    FunctionSpec(
        "dmc",
        fwi.vectorized_dmc,
        _wrap_all_but_last,
        _extract_single,
        lambda a: (cffdrs.duff_moisture_code(a[0], a[1], a[2], a[3], a[4], a[5], a[6]),),
        [50.0, 20.0, 40.0, 0.0, 55.0, 7, True],
        1,
    ),
    FunctionSpec(
        "ffmc",
        fwi.vectorized_ffmc,
        _wrap_all,
        _extract_single,
        lambda a: (cffdrs.fine_fuel_moisture_code(a[0], a[1], a[2], a[3], a[4]),),
        [88.0, 20.0, 40.0, 15.0, 0.0],
        1,
    ),
    FunctionSpec(
        "isi",
        fwi.vectorized_isi,
        _wrap_all_but_last,
        _extract_single,
        lambda a: (cffdrs.initial_spread_index(a[0], a[1], a[2]),),
        [88.0, 15.0, True],
        0,
    ),
    FunctionSpec(
        "fwi",
        fwi.vectorized_fwi,
        _wrap_all,
        _extract_single,
        lambda a: (cffdrs.fire_weather_index(a[0], a[1]),),
        [10.0, 40.0],
        0,
    ),
    # --- cffdrs_vec.fbp: self-contained (no fuel_type_code) ---
    FunctionSpec(
        "critical_surface_intensity",
        fbp.vectorized_critical_surface_intensity,
        _wrap_all,
        _extract_single,
        lambda a: (cffdrs.cfb_calc.critical_surface_intensity(a[0], a[1]),),
        [100.0, 3.0],
        0,
    ),
    FunctionSpec(
        "crown_fraction_burned",
        fbp.vectorized_crown_fraction_burned,
        _wrap_all,
        _extract_single,
        lambda a: (cffdrs.cfb_calc.crown_fraction_burned(a[0], a[1]),),
        [5.0, 1.0],
        0,
    ),
    FunctionSpec(
        "crown_rate_of_spread_c6",
        fbp.vectorized_crown_rate_of_spread_c6,
        _wrap_all,
        _extract_single,
        lambda a: (cffdrs.c6_calc.crown_rate_of_spread_c6(a[0], a[1]),),
        [10.0, 100.0],
        0,
    ),
    FunctionSpec(
        "intermediate_surface_rate_of_spread_c6",
        fbp.vectorized_intermediate_surface_rate_of_spread_c6,
        _wrap_all,
        _extract_single,
        lambda a: (cffdrs.c6_calc.intermediate_surface_rate_of_spread_c6(a[0]),),
        [10.0],
        0,
    ),
    FunctionSpec(
        "fire_intensity",
        fbp.vectorized_fire_intensity,
        _wrap_all,
        _extract_single,
        lambda a: (cffdrs.fire_intensity.fire_intensity(a[0], a[1]),),
        [2.0, 5.0],
        0,
    ),
    FunctionSpec(
        "foliar_moisture_content",
        fbp.vectorized_foliar_moisture_content,
        _wrap_all,
        _extract_single,
        lambda a: (cffdrs.foliar_moisture_content.foliar_moisture_content(a[0], a[1], a[2], a[3], a[4]),),
        [55.0, 120.0, 500.0, 180.0, 0.0],
        0,
    ),
    FunctionSpec(
        "surface_fire_rate_of_spread",
        fbp.vectorized_surface_fire_rate_of_spread,
        _wrap_all,
        _extract_single,
        lambda a: (cffdrs.cfb_calc.surface_fire_rate_of_spread(a[0], a[1]),),
        [100.0, 2.0],
        0,
    ),
    FunctionSpec(
        "surface_rate_of_spread_c6",
        fbp.vectorized_surface_rate_of_spread_c6,
        _wrap_all,
        _extract_single,
        lambda a: (cffdrs.c6_calc.surface_rate_of_spread_c6(a[0], a[1]),),
        [10.0, 40.0],
        0,
    ),
    FunctionSpec(
        "crown_fraction_burned_c6",
        fbp.vectorized_crown_fraction_burned_c6,
        _wrap_all,
        _extract_single,
        lambda a: (cffdrs.c6_calc.crown_fraction_burned_c6(a[0], a[1], a[2]),),
        [8.0, 4.0, 1.0],
        0,
    ),
    # --- cffdrs_vec.fbp: fuel_type_code first, then floats ---
    FunctionSpec(
        "distance_at_time",
        fbp.vectorized_distance_at_time,
        _wrap_all,
        _extract_single,
        lambda a: (cffdrs.distance_at_time.distance_at_time("C6", a[1], a[2], a[3]),),
        [C6, 5.0, 30.0, 0.5],
        1,
    ),
    FunctionSpec(
        "length_to_breadth",
        fbp.vectorized_length_to_breadth,
        _wrap_all,
        _extract_single,
        lambda a: (cffdrs.length_to_breadth.length_to_breadth("C6", a[1]),),
        [C6, 15.0],
        1,
    ),
    FunctionSpec(
        "length_to_breadth_at_time",
        fbp.vectorized_length_to_breadth_at_time,
        _wrap_all,
        _extract_single,
        lambda a: (cffdrs.length_to_breadth_at_time.length_to_breadth_at_time("C6", a[1], a[2], a[3]),),
        [C6, 1.5, 30.0, 0.5],
        1,
    ),
    FunctionSpec(
        "rate_of_spread_at_time",
        fbp.vectorized_rate_of_spread_at_time,
        _wrap_all,
        _extract_single,
        lambda a: (cffdrs.rate_of_spread_at_time.rate_of_spread_at_time("C6", a[1], a[2], a[3]),),
        [C6, 5.0, 30.0, 0.5],
        1,
    ),
    FunctionSpec(
        "surface_fuel_consumption",
        fbp.vectorized_surface_fuel_consumption,
        _wrap_all,
        _extract_single,
        lambda a: (cffdrs.surface_fuel_consumption.surface_fuel_consumption("C6", a[1], a[2], a[3], a[4]),),
        [C6, 88.0, 40.0, 50.0, 0.35],
        1,
    ),
    FunctionSpec(
        "total_fuel_consumption",
        fbp.vectorized_total_fuel_consumption,
        _wrap_all,
        _extract_single,
        lambda a: (cffdrs.total_fuel_consumption.total_fuel_consumption("C6", a[1], a[2], a[3], a[4], a[5]),),
        [C6, 1.0, 0.5, 2.0, 50.0, 30.0],
        1,
    ),
    FunctionSpec(
        "rate_of_spread",
        fbp.vectorized_rate_of_spread,
        _wrap_all,
        _extract_single,
        lambda a: (cffdrs.rate_of_spread.rate_of_spread("C6", a[1], a[2], a[3], a[4], a[5], a[6], a[7], a[8]),),
        [C6, 10.0, 40.0, 100.0, 2.0, 50.0, 30.0, 80.0, 3.0],
        1,
    ),
    FunctionSpec(
        "back_rate_of_spread",
        fbp.vectorized_back_rate_of_spread,
        _wrap_all,
        _extract_single,
        lambda a: (cffdrs.back_rate_of_spread.back_rate_of_spread("C6", a[1], a[2], a[3], a[4], a[5], a[6], a[7], a[8], a[9]),),
        [C6, 88.0, 40.0, 15.0, 100.0, 2.0, 50.0, 30.0, 80.0, 3.0],
        1,
    ),
    # --- cffdrs_vec.fbp: multi-output (guvectorize) ---
    FunctionSpec(
        "slope_adjustment",
        fbp.vectorized_slope_adjustment,
        _wrap_all,
        _extract_multi,
        lambda a: (
            lambda r: (r.wsv, r.raz)
        )(
            cffdrs.slope_calc.slope_adjustment(
                "C6", a[1], a[2], a[3], a[4], a[5], a[6], a[7], a[8], a[9], a[10], a[11], a[12], a[13]
            )
        ),
        [C6, 88.0, 40.0, 15.0, 1.2, 20.0, 0.5, 100.0, 2.0, 50.0, 30.0, 80.0, 3.0, 10.0],
        1,
    ),
    FunctionSpec(
        "rate_of_spread_extended",
        fbp.vectorized_rate_of_spread_extended,
        _wrap_all,
        _extract_multi,
        lambda a: (
            lambda r: (r.ros, r.cfb, r.csi, r.rso)
        )(
            cffdrs.rate_of_spread.rate_of_spread_extended("C6", a[1], a[2], a[3], a[4], a[5], a[6], a[7], a[8])
        ),
        [C6, 10.0, 40.0, 100.0, 2.0, 50.0, 30.0, 80.0, 3.0],
        1,
    ),
]


@pytest.mark.parametrize("spec", SPECS, ids=[s.id for s in SPECS])
def test_nan_propagates_like_reference(spec):
    args = list(spec.args)
    args[spec.swap_index] = float("nan")

    vec_result = spec.extract(spec.fn(*spec.prepare(args)))
    ref_result = spec.call_reference(args)

    np.testing.assert_allclose(vec_result, ref_result, equal_nan=True)


@pytest.mark.parametrize("spec", SPECS, ids=[s.id for s in SPECS])
def test_none_raises_clearly(spec):
    args = list(spec.args)
    args[spec.swap_index] = None
    prepared = spec.prepare(args)

    with pytest.raises(NONE_INPUT_ERRORS):
        spec.fn(*prepared)


def test_none_fuel_type_code_raises_clearly_vectorize_based():
    """fuel_type_code itself is also rejected as None, not just the float positions above -
    checked once each for a vectorize-based and a guvectorize-based function, since that's
    the mechanism that actually determines which exception type is raised (see module docstring).
    """
    prepared = [
        np.array([None]), np.array([10.0]), np.array([40.0]), np.array([100.0]), np.array([2.0]),
        np.array([50.0]), np.array([30.0]), np.array([80.0]), np.array([3.0]),
    ]
    with pytest.raises(NONE_INPUT_ERRORS):
        fbp.vectorized_rate_of_spread(*prepared)


def test_none_fuel_type_code_raises_clearly_guvectorize_based():
    prepared = [
        np.array([None]), np.array([10.0]), np.array([40.0]), np.array([100.0]), np.array([2.0]),
        np.array([50.0]), np.array([30.0]), np.array([80.0]), np.array([3.0]),
    ]
    with pytest.raises(NONE_INPUT_ERRORS):
        fbp.vectorized_rate_of_spread_extended(*prepared)
