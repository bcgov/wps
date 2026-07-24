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
dependency chain bottom-up, patching each function's globals so its internal
calls resolve to already-jitted versions. Naively, that means patching the
attributes on cffdrs's own modules (eg. cffdrs.rate_of_spread) - but those are
the exact same module objects the rest of the codebase imports (eg.
app.fire_behaviour.cffdrs calls the public, string-based API directly), so
doing that would make those callers transitively hit the jitted functions too.

Instead, every cffdrs module we need to patch is loaded as a private, isolated
copy via _isolated_clone() below - a second, independent module object that
nothing outside this file ever holds a reference to. Patching a clone's
namespace can't be observed by any other importer of cffdrs, at any time, so
there's nothing to revert and no window where another caller could see it.

A couple of the per-fuel-type lookup tables these functions index by
fuel_type_code (ROS_A, ROS_B, ROS_C0, BUI_O) mix Python int and float
literals, which numba types as a heterogeneous tuple - indexable only by a
compile-time constant, not a runtime fuel_type_code - so those get replaced
with homogeneous float64 arrays on the relevant clones too.

This reaches into cffdrs's private functions and constant tables, so it's
coupled to cffdrs's current internal call graph and table names. A cffdrs
upgrade that renames or restructures these will raise an AttributeError here
at import time rather than silently computing wrong values.
"""

import importlib.util

import cffdrs.back_rate_of_spread
import cffdrs.buildup_effect
import cffdrs.c6_calc
import cffdrs.cfb_calc
import cffdrs.constants as _constants_mod
import cffdrs.distance_at_time as _distance_at_time_mod
import cffdrs.fire_intensity as _fire_intensity_mod
import cffdrs.foliar_moisture_content as _foliar_moisture_content_mod
import cffdrs.fwi as _fwi_mod
import cffdrs.length_to_breadth as _length_to_breadth_mod
import cffdrs.length_to_breadth_at_time as _length_to_breadth_at_time_mod
import cffdrs.r_helpers as _r_helpers_mod
import cffdrs.rate_of_spread
import cffdrs.rate_of_spread_at_time as _rate_of_spread_at_time_mod
import cffdrs.slope_calc
import cffdrs.surface_fuel_consumption as _surface_fuel_consumption_mod
import cffdrs.total_fuel_consumption
import numpy as np
from numba import guvectorize, jit, vectorize


def _isolated_clone(module):
    """Load a private, independent copy of a cffdrs submodule that nothing outside this file
    ever references, so patching its namespace below can't be observed by any other importer
    of cffdrs. See module docstring for why that matters.
    """
    spec = importlib.util.spec_from_file_location(
        f"_cffdrs_vec_private_{module.__name__}", module.__file__
    )
    clone = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(clone)
    return clone


_back_rate_of_spread_mod = _isolated_clone(cffdrs.back_rate_of_spread)
_buildup_effect_mod = _isolated_clone(cffdrs.buildup_effect)
_c6_calc_mod = _isolated_clone(cffdrs.c6_calc)
_cfb_calc_mod = _isolated_clone(cffdrs.cfb_calc)
_rate_of_spread_mod = _isolated_clone(cffdrs.rate_of_spread)
_slope_calc_mod = _isolated_clone(cffdrs.slope_calc)
_total_fuel_consumption_mod = _isolated_clone(cffdrs.total_fuel_consumption)

# Homogeneous float64 views of the mixed int/float per-fuel-type tables, patched into every
# clone that indexes them by fuel_type_code inside a jitted function.
_ROS_A = np.asarray(_constants_mod.ROS_A, dtype=np.float64)
_ROS_B = np.asarray(_constants_mod.ROS_B, dtype=np.float64)
_ROS_C0 = np.asarray(_constants_mod.ROS_C0, dtype=np.float64)
_rate_of_spread_mod.ROS_A = _ROS_A
_rate_of_spread_mod.ROS_B = _ROS_B
_rate_of_spread_mod.ROS_C0 = _ROS_C0
_slope_calc_mod.ROS_A = _ROS_A
_slope_calc_mod.ROS_B = _ROS_B
_slope_calc_mod.ROS_C0 = _ROS_C0
_buildup_effect_mod.BUI_O = np.asarray(_constants_mod.BUI_O, dtype=np.float64)
_buildup_effect_mod.BUI_Q = np.asarray(_constants_mod.BUI_Q, dtype=np.float64)

# Level 0: leaf functions (only call math/numpy, safe to jit as-is)
_jit_safe_div = jit(_r_helpers_mod.safe_div)
_jit_buildup_effect = jit(_buildup_effect_mod._buildup_effect)
_jit_initial_spread_index = jit(_fwi_mod._initial_spread_index)
_jit_critical_surface_intensity = jit(_cfb_calc_mod.critical_surface_intensity)
_jit_crown_fraction_burned = jit(_cfb_calc_mod.crown_fraction_burned)
_jit_crown_rate_of_spread_c6 = jit(_c6_calc_mod.crown_rate_of_spread_c6)
_jit_intermediate_surface_rate_of_spread_c6 = jit(
    _c6_calc_mod.intermediate_surface_rate_of_spread_c6
)
_jit_rate_of_spread_c6 = jit(_c6_calc_mod.rate_of_spread_c6)
_jit_crown_fuel_consumption = jit(_total_fuel_consumption_mod._crown_fuel_consumption)
_jit_floored_basic_rsi = jit(_rate_of_spread_mod._floored_basic_rsi)

# Level 1: functions that call only level-0 functions
_cfb_calc_mod.safe_div = _jit_safe_div
_jit_surface_fire_rate_of_spread = jit(_cfb_calc_mod.surface_fire_rate_of_spread)

_c6_calc_mod._buildup_effect = _jit_buildup_effect
_c6_calc_mod.crown_fraction_burned = _jit_crown_fraction_burned
_jit_surface_rate_of_spread_c6 = jit(_c6_calc_mod._surface_rate_of_spread_c6)
_jit_crown_fraction_burned_c6 = jit(_c6_calc_mod.crown_fraction_burned_c6)

_total_fuel_consumption_mod._crown_fuel_consumption = _jit_crown_fuel_consumption
_jit_total_fuel_consumption = jit(_total_fuel_consumption_mod._total_fuel_consumption)

# Level 2: _rate_of_spread_extended, pulling most of the above together
_rate_of_spread_mod._floored_basic_rsi = _jit_floored_basic_rsi
_rate_of_spread_mod.intermediate_surface_rate_of_spread_c6 = (
    _jit_intermediate_surface_rate_of_spread_c6
)
_rate_of_spread_mod.crown_rate_of_spread_c6 = _jit_crown_rate_of_spread_c6
_rate_of_spread_mod._surface_rate_of_spread_c6 = _jit_surface_rate_of_spread_c6
_rate_of_spread_mod.crown_fraction_burned_c6 = _jit_crown_fraction_burned_c6
_rate_of_spread_mod.rate_of_spread_c6 = _jit_rate_of_spread_c6
_rate_of_spread_mod.critical_surface_intensity = _jit_critical_surface_intensity
_rate_of_spread_mod.surface_fire_rate_of_spread = _jit_surface_fire_rate_of_spread
_rate_of_spread_mod.crown_fraction_burned = _jit_crown_fraction_burned
_rate_of_spread_mod._buildup_effect = _jit_buildup_effect
_jit_rate_of_spread_extended = jit(_rate_of_spread_mod._rate_of_spread_extended)
_rate_of_spread_mod._rate_of_spread_extended = _jit_rate_of_spread_extended

# Level 3: _rate_of_spread, and the modules that call it
_jit_rate_of_spread = jit(_rate_of_spread_mod._rate_of_spread)
_back_rate_of_spread_mod._rate_of_spread = _jit_rate_of_spread
_slope_calc_mod._rate_of_spread = _jit_rate_of_spread
_slope_calc_mod._initial_spread_index = _jit_initial_spread_index
_slope_calc_mod.safe_div = _jit_safe_div
_jit_slope_adjustment = jit(_slope_calc_mod._slope_adjustment)

# Public vectorized ufuncs

# Self-contained functions: same one-line pattern as cffdrs_vec/fwi.py - these read directly
# from cffdrs's normal (non-cloned) modules, since there's nothing to patch on them.
vectorized_critical_surface_intensity = vectorize(cffdrs.cfb_calc.critical_surface_intensity)
vectorized_crown_fraction_burned = vectorize(cffdrs.cfb_calc.crown_fraction_burned)
vectorized_crown_rate_of_spread_c6 = vectorize(cffdrs.c6_calc.crown_rate_of_spread_c6)
vectorized_intermediate_surface_rate_of_spread_c6 = vectorize(
    cffdrs.c6_calc.intermediate_surface_rate_of_spread_c6
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

# Composite functions: vectorized from the patched-and-jitted clones above
vectorized_surface_fire_rate_of_spread = vectorize(_cfb_calc_mod.surface_fire_rate_of_spread)
vectorized_surface_rate_of_spread_c6 = vectorize(_c6_calc_mod._surface_rate_of_spread_c6)
vectorized_crown_fraction_burned_c6 = vectorize(_c6_calc_mod.crown_fraction_burned_c6)
vectorized_total_fuel_consumption = vectorize(_total_fuel_consumption_mod._total_fuel_consumption)
vectorized_rate_of_spread = vectorize(_rate_of_spread_mod._rate_of_spread)
vectorized_back_rate_of_spread = vectorize(_back_rate_of_spread_mod._back_rate_of_spread)


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
