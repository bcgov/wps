"""Numba-vectorized wrappers for cffdrs Fire Behaviour Prediction (FBP) functions.

cffdrs ships plain-Python "vectorization-ready" functions for FBP calculations
that branch on fuel type: a leading-underscore sibling that takes an int
fuel_type_code (see cffdrs.constants.FUEL_TYPE_CODES) instead of a fuel type
string, with no recursive/string-dispatch fuel-type branching in the way numba
can't trace. That's enough for numba to vectorize the self-contained ones
directly (the same one-line `vectorize(fn)` pattern as cffdrs_vec/fwi.py), but
several of them still call other plain-Python cffdrs functions internally
(e.g. rate_of_spread -> rate_of_spread_extended -> surface_fire_rate_of_spread
-> safe_div), and numba's nopython mode can't compile a call into a function
it hasn't itself compiled.

To vectorize those composite functions too, we jit-compile the whole
dependency chain bottom-up: for each one, we temporarily patch its cffdrs
module's own namespace so its internal calls resolve to already-jitted
versions, eagerly compile it with an explicit signature (eager, because a
lazily-compiled function only resolves its globals - including those
patches - on first call, which could happen after we've reverted them), and
then immediately revert the module back to its original, unpatched
functions. A couple of the per-fuel-type lookup tables those functions index
by fuel_type_code (ROS_A, ROS_B, ROS_C0, BUI_O) mix Python int and float
literals, which numba types as a heterogeneous tuple - indexable only by a
compile-time constant, not a runtime fuel_type_code - so those get the same
temporary-patch treatment, as homogeneous float64 arrays.

The revert step matters: cffdrs's own modules are shared with the rest of
the codebase (eg. app.fire_behaviour.cffdrs calls the public, string-based
API directly). Leaving them patched would mean those callers transitively
hit the same jitted functions - which, unlike plain Python, must type-check
every branch up front even ones the actual fuel type never takes, so a
perfectly normal call like rate_of_spread("C1", ..., pc=None) (pc is only
used by the M1-M4 branches) would fail to compile instead of just skipping
that branch as it does in plain Python.

This reaches into cffdrs's private functions and constant tables, so it's
coupled to cffdrs's current internal call graph and table names. A cffdrs
upgrade that renames or restructures these will raise an AttributeError here
at import time rather than silently computing wrong values.
"""

from contextlib import contextmanager

import numpy as np
from numba import float64, guvectorize, int64, jit, vectorize

import cffdrs.back_rate_of_spread as _back_rate_of_spread_mod
import cffdrs.buildup_effect as _buildup_effect_mod
import cffdrs.c6_calc as _c6_calc_mod
import cffdrs.cfb_calc as _cfb_calc_mod
import cffdrs.constants as _constants_mod
import cffdrs.distance_at_time as _distance_at_time_mod
import cffdrs.fire_intensity as _fire_intensity_mod
import cffdrs.foliar_moisture_content as _foliar_moisture_content_mod
import cffdrs.fwi as _fwi_mod
import cffdrs.length_to_breadth as _length_to_breadth_mod
import cffdrs.length_to_breadth_at_time as _length_to_breadth_at_time_mod
import cffdrs.r_helpers as _r_helpers_mod
import cffdrs.rate_of_spread as _rate_of_spread_mod
import cffdrs.rate_of_spread_at_time as _rate_of_spread_at_time_mod
import cffdrs.slope_calc as _slope_calc_mod
import cffdrs.surface_fuel_consumption as _surface_fuel_consumption_mod
import cffdrs.total_fuel_consumption as _total_fuel_consumption_mod

_I = int64
_F = float64


@contextmanager
def _temporarily_patched(module, **patches):
    """Patch `module`'s attributes with `patches` for the duration of the `with` block (eg. for
    compiling a jitted function whose internal calls need to resolve to jitted dependencies),
    then restore the module's original attributes - see module docstring for why the revert
    matters.
    """
    originals = {name: getattr(module, name) for name in patches}
    for name, value in patches.items():
        setattr(module, name, value)
    try:
        yield
    finally:
        for name, original in originals.items():
            setattr(module, name, original)


# Level 0: leaf functions (only call math/numpy - no patching needed, just an explicit
# signature so they're compiled once here rather than lazily wherever they're first called).
_jit_safe_div = jit((_F, _F))(_r_helpers_mod.safe_div)
# Left lazy (no explicit signature): _slope_adjustment calls this with only 2 args, relying on
# its fbp_mod=False default, and an eager signature would require an exact arity match.
_jit_initial_spread_index = jit(_fwi_mod._initial_spread_index)
_jit_critical_surface_intensity = jit((_F, _F))(_cfb_calc_mod.critical_surface_intensity)
_jit_crown_fraction_burned = jit((_F, _F))(_cfb_calc_mod.crown_fraction_burned)
_jit_crown_rate_of_spread_c6 = jit((_F, _F))(_c6_calc_mod.crown_rate_of_spread_c6)
_jit_intermediate_surface_rate_of_spread_c6 = jit((_F,))(
    _c6_calc_mod.intermediate_surface_rate_of_spread_c6
)
_jit_rate_of_spread_c6 = jit((_F, _F, _F))(_c6_calc_mod.rate_of_spread_c6)
_jit_crown_fuel_consumption = jit((_I, _F, _F, _F, _F))(
    _total_fuel_consumption_mod._crown_fuel_consumption
)

_BUI_O = np.asarray(_constants_mod.BUI_O, dtype=np.float64)
_BUI_Q = np.asarray(_constants_mod.BUI_Q, dtype=np.float64)
with _temporarily_patched(_buildup_effect_mod, BUI_O=_BUI_O, BUI_Q=_BUI_Q):
    _jit_buildup_effect = jit((_I, _F))(_buildup_effect_mod._buildup_effect)

_ROS_A = np.asarray(_constants_mod.ROS_A, dtype=np.float64)
_ROS_B = np.asarray(_constants_mod.ROS_B, dtype=np.float64)
_ROS_C0 = np.asarray(_constants_mod.ROS_C0, dtype=np.float64)
with _temporarily_patched(_rate_of_spread_mod, ROS_A=_ROS_A, ROS_B=_ROS_B, ROS_C0=_ROS_C0):
    _jit_floored_basic_rsi = jit((_I, _F))(_rate_of_spread_mod._floored_basic_rsi)

    # Level 1: functions that call only level-0 functions
    with _temporarily_patched(_cfb_calc_mod, safe_div=_jit_safe_div):
        _jit_surface_fire_rate_of_spread = jit((_F, _F))(
            _cfb_calc_mod.surface_fire_rate_of_spread
        )

    with _temporarily_patched(
        _c6_calc_mod,
        _buildup_effect=_jit_buildup_effect,
        crown_fraction_burned=_jit_crown_fraction_burned,
    ):
        _jit_surface_rate_of_spread_c6 = jit((_F, _F))(_c6_calc_mod._surface_rate_of_spread_c6)
        _jit_crown_fraction_burned_c6 = jit((_F, _F, _F))(_c6_calc_mod.crown_fraction_burned_c6)

    with _temporarily_patched(
        _total_fuel_consumption_mod, _crown_fuel_consumption=_jit_crown_fuel_consumption
    ):
        _jit_total_fuel_consumption = jit((_I, _F, _F, _F, _F, _F))(
            _total_fuel_consumption_mod._total_fuel_consumption
        )

    # Level 2: _rate_of_spread_extended, pulling most of the above together
    with _temporarily_patched(
        _rate_of_spread_mod,
        _floored_basic_rsi=_jit_floored_basic_rsi,
        intermediate_surface_rate_of_spread_c6=_jit_intermediate_surface_rate_of_spread_c6,
        crown_rate_of_spread_c6=_jit_crown_rate_of_spread_c6,
        _surface_rate_of_spread_c6=_jit_surface_rate_of_spread_c6,
        crown_fraction_burned_c6=_jit_crown_fraction_burned_c6,
        rate_of_spread_c6=_jit_rate_of_spread_c6,
        critical_surface_intensity=_jit_critical_surface_intensity,
        surface_fire_rate_of_spread=_jit_surface_fire_rate_of_spread,
        crown_fraction_burned=_jit_crown_fraction_burned,
        _buildup_effect=_jit_buildup_effect,
    ):
        _jit_rate_of_spread_extended = jit((_I, _F, _F, _F, _F, _F, _F, _F, _F))(
            _rate_of_spread_mod._rate_of_spread_extended
        )

# Level 3: _rate_of_spread, and the modules that call it
with _temporarily_patched(
    _rate_of_spread_mod, _rate_of_spread_extended=_jit_rate_of_spread_extended
):
    _jit_rate_of_spread = jit((_I, _F, _F, _F, _F, _F, _F, _F, _F))(
        _rate_of_spread_mod._rate_of_spread
    )
    vectorized_rate_of_spread = vectorize(
        [_F(_I, _F, _F, _F, _F, _F, _F, _F, _F)]
    )(_rate_of_spread_mod._rate_of_spread)

with _temporarily_patched(_back_rate_of_spread_mod, _rate_of_spread=_jit_rate_of_spread):
    vectorized_back_rate_of_spread = vectorize(
        [_F(_I, _F, _F, _F, _F, _F, _F, _F, _F, _F)]
    )(_back_rate_of_spread_mod._back_rate_of_spread)

with _temporarily_patched(
    _slope_calc_mod,
    _rate_of_spread=_jit_rate_of_spread,
    _initial_spread_index=_jit_initial_spread_index,
    safe_div=_jit_safe_div,
    ROS_A=_ROS_A,
    ROS_B=_ROS_B,
    ROS_C0=_ROS_C0,
):
    _jit_slope_adjustment = jit((_I, _F, _F, _F, _F, _F, _F, _F, _F, _F, _F, _F, _F, _F))(
        _slope_calc_mod._slope_adjustment
    )

with _temporarily_patched(
    _total_fuel_consumption_mod, _crown_fuel_consumption=_jit_crown_fuel_consumption
):
    vectorized_total_fuel_consumption = vectorize(
        [_F(_I, _F, _F, _F, _F, _F)]
    )(_total_fuel_consumption_mod._total_fuel_consumption)

with _temporarily_patched(_cfb_calc_mod, safe_div=_jit_safe_div):
    vectorized_surface_fire_rate_of_spread = vectorize(
        [_F(_F, _F)]
    )(_cfb_calc_mod.surface_fire_rate_of_spread)

with _temporarily_patched(_c6_calc_mod, _buildup_effect=_jit_buildup_effect):
    vectorized_surface_rate_of_spread_c6 = vectorize(
        [_F(_F, _F)]
    )(_c6_calc_mod._surface_rate_of_spread_c6)

with _temporarily_patched(_c6_calc_mod, crown_fraction_burned=_jit_crown_fraction_burned):
    vectorized_crown_fraction_burned_c6 = vectorize(
        [_F(_F, _F, _F)]
    )(_c6_calc_mod.crown_fraction_burned_c6)


# Self-contained functions: same one-line pattern as cffdrs_vec/fwi.py - no patching needed.
vectorized_critical_surface_intensity = vectorize(_cfb_calc_mod.critical_surface_intensity)
vectorized_crown_fraction_burned = vectorize(_cfb_calc_mod.crown_fraction_burned)
vectorized_crown_rate_of_spread_c6 = vectorize(_c6_calc_mod.crown_rate_of_spread_c6)
vectorized_intermediate_surface_rate_of_spread_c6 = vectorize(
    _c6_calc_mod.intermediate_surface_rate_of_spread_c6
)
vectorized_distance_at_time = vectorize(_distance_at_time_mod._distance_at_time)
vectorized_fire_intensity = vectorize(_fire_intensity_mod.fire_intensity)
vectorized_foliar_moisture_content = vectorize(_foliar_moisture_content_mod.foliar_moisture_content)
vectorized_length_to_breadth = vectorize(_length_to_breadth_mod._length_to_breadth)
vectorized_length_to_breadth_at_time = vectorize(
    _length_to_breadth_at_time_mod._length_to_breadth_at_time
)
vectorized_rate_of_spread_at_time = vectorize(_rate_of_spread_at_time_mod._rate_of_spread_at_time)
vectorized_surface_fuel_consumption = vectorize(
    _surface_fuel_consumption_mod._surface_fuel_consumption
)


@guvectorize(
    [
        "void(int64, float64, float64, float64, float64, float64, float64, float64,"
        " float64, float64, float64, float64, float64, float64, float64[:], float64[:])"
    ],
    "(),(),(),(),(),(),(),(),(),(),(),(),(),()->(),()",
)
def vectorized_slope_adjustment(
    fuel_type_code, ffmc, bui, ws, waz, gs, saz, fmc, sfc, pc, pdf, cc, cbh, isi, wsv_out, raz_out
):
    result = _jit_slope_adjustment(
        fuel_type_code, ffmc, bui, ws, waz, gs, saz, fmc, sfc, pc, pdf, cc, cbh, isi
    )
    wsv_out[0] = result.wsv
    raz_out[0] = result.raz


@guvectorize(
    [
        "void(int64, float64, float64, float64, float64, float64, float64, float64,"
        " float64, float64[:], float64[:], float64[:], float64[:])"
    ],
    "(),(),(),(),(),(),(),(),()->(),(),(),()",
)
def vectorized_rate_of_spread_extended(
    fuel_type_code, isi, bui, fmc, sfc, pc, pdf, cc, cbh, ros_out, cfb_out, csi_out, rso_out
):
    """Same as vectorized_rate_of_spread, but also returns CFB, CSI and RSO.

    These are computed as a side effect of rate_of_spread_extended() regardless (C6's ROS
    depends on its own CFB), so exposing them here is free - no additional jitting needed.
    """
    result = _jit_rate_of_spread_extended(fuel_type_code, isi, bui, fmc, sfc, pc, pdf, cc, cbh)
    ros_out[0] = result.ros
    cfb_out[0] = result.cfb
    csi_out[0] = result.csi
    rso_out[0] = result.rso
