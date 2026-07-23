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
dependency chain bottom-up and patch each cffdrs module's own namespace so its
internal calls resolve to the jitted versions. A couple of the per-fuel-type
lookup tables those functions index by fuel_type_code (ROS_A, ROS_B, ROS_C0,
BUI_O) mix Python int and float literals, which numba types as a
heterogeneous tuple - indexable only by a compile-time constant, not by a
runtime fuel_type_code, so those get patched too, as homogeneous float64
arrays.

This reaches into cffdrs's private functions and constant tables, so it's
coupled to cffdrs's current internal call graph and table names. A cffdrs
upgrade that renames or restructures these will raise an AttributeError here
at import time rather than silently computing wrong values.
"""

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
import numpy as np
from numba import guvectorize, jit, vectorize

# Homogeneous float64 views of the mixed int/float per-fuel-type tables, patched
# into every module that indexes them by fuel_type_code inside a jitted function.
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

# Level 2: _rate_of_spread_extended, pulling most of the above together ---
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
_rate_of_spread_mod._rate_of_spread_extended = jit(_rate_of_spread_mod._rate_of_spread_extended)

# Level 3: _rate_of_spread, and the modules that call it
_jit_rate_of_spread = jit(_rate_of_spread_mod._rate_of_spread)
_back_rate_of_spread_mod._rate_of_spread = _jit_rate_of_spread
_slope_calc_mod._rate_of_spread = _jit_rate_of_spread
_slope_calc_mod._initial_spread_index = _jit_initial_spread_index
_slope_calc_mod.safe_div = _jit_safe_div
_jit_slope_adjustment = jit(_slope_calc_mod._slope_adjustment)

# Public vectorized ufuncs

# Self-contained functions: same one-line pattern as cffdrs_vec/fwi.py
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

# Composite functions: vectorized from the patched-and-jitted chain above
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
