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
from types import MappingProxyType
from typing import NamedTuple

import cffdrs.back_rate_of_spread
import cffdrs.buildup_effect
import cffdrs.c6_calc
import cffdrs.cfb_calc
import cffdrs.constants as _constants_mod
import cffdrs.crown_base_height
import cffdrs.crown_fuel_load
import cffdrs.distance_at_time as _distance_at_time_mod
import cffdrs.fire_behaviour_prediction
import cffdrs.fire_intensity as _fire_intensity_mod
import cffdrs.flank_rate_of_spread as _flank_rate_of_spread_mod
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


# expose the codes consumed by the vectorized functions without making callers depend on
# cffdrs's private module layout or duplicate its zero-based values.
FUEL_TYPE_CODES = MappingProxyType(dict(_constants_mod.FUEL_TYPE_CODES))


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
_crown_base_height_mod = _isolated_clone(cffdrs.crown_base_height)
_crown_fuel_load_mod = _isolated_clone(cffdrs.crown_fuel_load)
_fire_behaviour_prediction_mod = _isolated_clone(cffdrs.fire_behaviour_prediction)
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
_crown_base_height_mod.CBH_DEFAULT = np.asarray(
    _crown_base_height_mod.CBH_DEFAULT, dtype=np.float64
)
_crown_fuel_load_mod.CFL_DEFAULT = np.asarray(_crown_fuel_load_mod.CFL_DEFAULT, dtype=np.float64)

# Level 0: leaf functions (only call math/numpy, safe to jit as-is)
_jit_safe_div = jit(_r_helpers_mod.safe_div)
_jit_buildup_effect = jit(_buildup_effect_mod._buildup_effect)
_jit_initial_spread_index = jit(_fwi_mod.initial_spread_index)
_jit_critical_surface_intensity = jit(_cfb_calc_mod.critical_surface_intensity)
_jit_crown_fraction_burned = jit(_cfb_calc_mod.crown_fraction_burned)
_jit_crown_rate_of_spread_c6 = jit(_c6_calc_mod.crown_rate_of_spread_c6)
_jit_intermediate_surface_rate_of_spread_c6 = jit(
    _c6_calc_mod.intermediate_surface_rate_of_spread_c6
)
_jit_rate_of_spread_c6 = jit(_c6_calc_mod.rate_of_spread_c6)
_jit_crown_fuel_consumption = jit(_total_fuel_consumption_mod._crown_fuel_consumption)
_jit_floored_basic_rsi = jit(_rate_of_spread_mod._floored_basic_rsi)
_jit_crown_base_height = jit(_crown_base_height_mod._crown_base_height)
_jit_crown_fuel_load = jit(_crown_fuel_load_mod._crown_fuel_load)
_jit_foliar_moisture_content = jit(_foliar_moisture_content_mod.foliar_moisture_content)
_jit_surface_fuel_consumption = jit(_surface_fuel_consumption_mod._surface_fuel_consumption)
_jit_fire_intensity = jit(_fire_intensity_mod.fire_intensity)
_jit_length_to_breadth = jit(_length_to_breadth_mod._length_to_breadth)
_jit_length_to_breadth_at_time = jit(_length_to_breadth_at_time_mod._length_to_breadth_at_time)
_jit_flank_rate_of_spread = jit(_flank_rate_of_spread_mod.flank_rate_of_spread)
_jit_rate_of_spread_at_time = jit(_rate_of_spread_at_time_mod._rate_of_spread_at_time)
_jit_distance_at_time = jit(_distance_at_time_mod._distance_at_time)

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
_slope_calc_mod.initial_spread_index = _jit_initial_spread_index
_slope_calc_mod.safe_div = _jit_safe_div
_jit_slope_adjustment = jit(_slope_calc_mod._slope_adjustment)

# Level 4: _back_rate_of_spread (reuses the _rate_of_spread patch from Level 3 above)
_jit_back_rate_of_spread = jit(_back_rate_of_spread_mod._back_rate_of_spread)

# Level 5: _fire_behaviour_prediction, pulling every level above together plus the handful of
# leaf functions unique to it.
_fire_behaviour_prediction_mod._crown_base_height = _jit_crown_base_height
_fire_behaviour_prediction_mod._crown_fuel_load = _jit_crown_fuel_load
_fire_behaviour_prediction_mod.foliar_moisture_content = _jit_foliar_moisture_content
_fire_behaviour_prediction_mod._surface_fuel_consumption = _jit_surface_fuel_consumption
_fire_behaviour_prediction_mod.initial_spread_index = _jit_initial_spread_index
_fire_behaviour_prediction_mod._slope_adjustment = _jit_slope_adjustment
_fire_behaviour_prediction_mod._rate_of_spread_extended = _jit_rate_of_spread_extended
_fire_behaviour_prediction_mod._total_fuel_consumption = _jit_total_fuel_consumption
_fire_behaviour_prediction_mod.fire_intensity = _jit_fire_intensity
_fire_behaviour_prediction_mod._buildup_effect = _jit_buildup_effect
_fire_behaviour_prediction_mod._length_to_breadth = _jit_length_to_breadth
_fire_behaviour_prediction_mod._length_to_breadth_at_time = _jit_length_to_breadth_at_time
_fire_behaviour_prediction_mod._back_rate_of_spread = _jit_back_rate_of_spread
_fire_behaviour_prediction_mod.flank_rate_of_spread = _jit_flank_rate_of_spread
_fire_behaviour_prediction_mod._rate_of_spread_at_time = _jit_rate_of_spread_at_time
_fire_behaviour_prediction_mod.crown_fraction_burned = _jit_crown_fraction_burned
_fire_behaviour_prediction_mod._crown_fuel_consumption = _jit_crown_fuel_consumption
_fire_behaviour_prediction_mod._distance_at_time = _jit_distance_at_time
_jit_fire_behaviour_prediction = jit(_fire_behaviour_prediction_mod._fire_behaviour_prediction)

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


# _fire_behaviour_prediction's real signature (26 params) and _FBPOutput's real fields (44,
# always all computed - see _jit_fire_behaviour_prediction's docstring) are pulled from the
# clone itself, rather than hand-counted, so a cffdrs upgrade that adds/removes/reorders either
# one breaks loudly here (wrong arg count to `void(...)`) instead of silently misaligning the
# bodies below.
_FBP_OUTPUT_FIELDS = _fire_behaviour_prediction_mod._FBPOutput._fields

# A single guvectorize returning all 44 _FBPOutput fields would need 26+44=70 operands, over
# numpy's hard 64-operand-per-ufunc limit - so the two private guvectorize functions below split
# it in two, along the same Primary/Secondary line fire_behaviour_prediction(input, "All") itself
# draws (FBPPrimaryOutput's 8 fields in _vectorized_fbp_primary, everything else - including
# wsv0/raz0, which aren't part of Primary/Secondary/All at all - in _vectorized_fbp_secondary).
# vectorized_fire_behaviour_prediction (the public function below both) calls both and merges
# them into one FBPOutput, so callers see a single call returning every field, same as
# _fire_behaviour_prediction itself - at the cost of running _jit_fire_behaviour_prediction twice
# per element, since each half independently calls it.
_FBP_PRIMARY_FIELDS = ("cfb", "cfc", "fd_code", "hfi", "raz", "ros", "sfc", "tfc")
_FBP_SECONDARY_FIELDS = tuple(f for f in _FBP_OUTPUT_FIELDS if f not in _FBP_PRIMARY_FIELDS)
assert set(_FBP_PRIMARY_FIELDS) | set(_FBP_SECONDARY_FIELDS) == set(_FBP_OUTPUT_FIELDS)


# Same 26 inputs as _jit_fire_behaviour_prediction (fuel_type_code, ffmc, bui, ws, wd_rad, gs,
# aspect_rad, pc, pdf, cc, gfl, cbh, cfl, fmc, isi, lat, lon, elv, dj, d0, sd, sh, hr, theta_rad,
# accel, buieff) on every guvectorize below - only the trailing output types/layout differ,
# matching _FBP_PRIMARY_FIELDS/_FBP_SECONDARY_FIELDS field-for-field (fd_code is int64, like
# fuel_type_code; everything else is float64).
@guvectorize(
    [
        "void(int64, float64, float64, float64, float64, float64, float64, float64, float64,"
        " float64, float64, float64, float64, float64, float64, float64, float64, float64,"
        " float64, float64, float64, float64, float64, float64, int64, int64,"
        " float64[:], float64[:], int64[:], float64[:], float64[:], float64[:], float64[:],"
        " float64[:])"
    ],
    "(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),()"
    "->(),(),(),(),(),(),(),()",
)
def _vectorized_fbp_primary(
    fuel_type_code,
    ffmc,
    bui,
    ws,
    wd_rad,
    gs,
    aspect_rad,
    pc,
    pdf,
    cc,
    gfl,
    cbh,
    cfl,
    fmc,
    isi,
    lat,
    lon,
    elv,
    dj,
    d0,
    sd,
    sh,
    hr,
    theta_rad,
    accel,
    buieff,
    cfb_out,
    cfc_out,
    fd_code_out,
    hfi_out,
    raz_out,
    ros_out,
    sfc_out,
    tfc_out,
):
    """The 8 FBPPrimaryOutput fields half of vectorized_fire_behaviour_prediction below - see
    its docstring and the comment above _FBP_PRIMARY_FIELDS for why this is split in two.
    """
    result = _jit_fire_behaviour_prediction(
        fuel_type_code,
        ffmc,
        bui,
        ws,
        wd_rad,
        gs,
        aspect_rad,
        pc,
        pdf,
        cc,
        gfl,
        cbh,
        cfl,
        fmc,
        isi,
        lat,
        lon,
        elv,
        dj,
        d0,
        sd,
        sh,
        hr,
        theta_rad,
        accel,
        buieff,
    )
    cfb_out[0] = result.cfb
    cfc_out[0] = result.cfc
    fd_code_out[0] = result.fd_code
    hfi_out[0] = result.hfi
    raz_out[0] = result.raz
    ros_out[0] = result.ros
    sfc_out[0] = result.sfc
    tfc_out[0] = result.tfc


@guvectorize(
    [
        "void(int64, float64, float64, float64, float64, float64, float64, float64, float64,"
        " float64, float64, float64, float64, float64, float64, float64, float64, float64,"
        " float64, float64, float64, float64, float64, float64, int64, int64, float64[:],"
        " float64[:], float64[:], float64[:], float64[:], float64[:], float64[:], float64[:],"
        " float64[:], float64[:], float64[:], float64[:], float64[:], float64[:], float64[:],"
        " float64[:], float64[:], float64[:], float64[:], float64[:], float64[:], float64[:],"
        " float64[:], float64[:], float64[:], float64[:], float64[:], float64[:], float64[:],"
        " float64[:], float64[:], float64[:], float64[:], float64[:], float64[:], float64[:])"
    ],
    "(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),()->(),(),(),()"
    ",(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),(),()"
    ",(),()",
)
def _vectorized_fbp_secondary(
    fuel_type_code,
    ffmc,
    bui,
    ws,
    wd_rad,
    gs,
    aspect_rad,
    pc,
    pdf,
    cc,
    gfl,
    cbh,
    cfl,
    fmc,
    isi,
    lat,
    lon,
    elv,
    dj,
    d0,
    sd,
    sh,
    hr,
    theta_rad,
    accel,
    buieff,
    be_out,
    sf_out,
    isi_out,
    ffmc_out,
    fmc_out,
    d0_out,
    rso_out,
    csi_out,
    fros_out,
    bros_out,
    hrost_out,
    frost_out,
    brost_out,
    fcfb_out,
    bcfb_out,
    ffi_out,
    bfi_out,
    ftfc_out,
    btfc_out,
    ti_out,
    fti_out,
    bti_out,
    lb_out,
    lbt_out,
    wsv_out,
    dh_out,
    db_out,
    df_out,
    tros_out,
    trost_out,
    tcfb_out,
    tfi_out,
    ttfc_out,
    tti_out,
    wsv0_out,
    raz0_out,
):
    """The other 36 _FBPOutput fields half of vectorized_fire_behaviour_prediction below,
    including wsv0/raz0 (the raw, pre-fallback slope_adjustment() outputs - exposed by
    fire_behaviour_prediction()'s output="WSV0"/"RAZ0" shortcuts, not part of Primary/Secondary/
    All). See vectorized_fire_behaviour_prediction's docstring for everything else.
    """
    result = _jit_fire_behaviour_prediction(
        fuel_type_code,
        ffmc,
        bui,
        ws,
        wd_rad,
        gs,
        aspect_rad,
        pc,
        pdf,
        cc,
        gfl,
        cbh,
        cfl,
        fmc,
        isi,
        lat,
        lon,
        elv,
        dj,
        d0,
        sd,
        sh,
        hr,
        theta_rad,
        accel,
        buieff,
    )
    be_out[0] = result.be
    sf_out[0] = result.sf
    isi_out[0] = result.isi
    ffmc_out[0] = result.ffmc
    fmc_out[0] = result.fmc
    d0_out[0] = result.d0
    rso_out[0] = result.rso
    csi_out[0] = result.csi
    fros_out[0] = result.fros
    bros_out[0] = result.bros
    hrost_out[0] = result.hrost
    frost_out[0] = result.frost
    brost_out[0] = result.brost
    fcfb_out[0] = result.fcfb
    bcfb_out[0] = result.bcfb
    ffi_out[0] = result.ffi
    bfi_out[0] = result.bfi
    ftfc_out[0] = result.ftfc
    btfc_out[0] = result.btfc
    ti_out[0] = result.ti
    fti_out[0] = result.fti
    bti_out[0] = result.bti
    lb_out[0] = result.lb
    lbt_out[0] = result.lbt
    wsv_out[0] = result.wsv
    dh_out[0] = result.dh
    db_out[0] = result.db
    df_out[0] = result.df
    tros_out[0] = result.tros
    trost_out[0] = result.trost
    tcfb_out[0] = result.tcfb
    tfi_out[0] = result.tfi
    ttfc_out[0] = result.ttfc
    tti_out[0] = result.tti
    wsv0_out[0] = result.wsv0
    raz0_out[0] = result.raz0


class FBPPrimaryOutput(NamedTuple):
    """The primary fields from one vectorized CFFDRS fire behaviour calculation."""

    cfb: np.ndarray
    cfc: np.ndarray
    fd_code: np.ndarray
    hfi: np.ndarray
    raz: np.ndarray
    ros: np.ndarray
    sfc: np.ndarray
    tfc: np.ndarray


class FBPOutput(NamedTuple):
    """Every field cffdrs's own _fire_behaviour_prediction computes and returns - Primary (cfb
    through tfc) and Secondary (be through tti), plus wsv0/raz0 (the raw, pre-fallback
    slope_adjustment() outputs, not part of Primary/Secondary/All - see
    _vectorized_fbp_secondary's docstring). Field order matches _FBPOutput exactly.
    """

    cfb: np.ndarray
    cfc: np.ndarray
    fd_code: np.ndarray
    hfi: np.ndarray
    raz: np.ndarray
    ros: np.ndarray
    sfc: np.ndarray
    tfc: np.ndarray
    be: np.ndarray
    sf: np.ndarray
    isi: np.ndarray
    ffmc: np.ndarray
    fmc: np.ndarray
    d0: np.ndarray
    rso: np.ndarray
    csi: np.ndarray
    fros: np.ndarray
    bros: np.ndarray
    hrost: np.ndarray
    frost: np.ndarray
    brost: np.ndarray
    fcfb: np.ndarray
    bcfb: np.ndarray
    ffi: np.ndarray
    bfi: np.ndarray
    ftfc: np.ndarray
    btfc: np.ndarray
    ti: np.ndarray
    fti: np.ndarray
    bti: np.ndarray
    lb: np.ndarray
    lbt: np.ndarray
    wsv: np.ndarray
    dh: np.ndarray
    db: np.ndarray
    df: np.ndarray
    tros: np.ndarray
    trost: np.ndarray
    tcfb: np.ndarray
    tfi: np.ndarray
    ttfc: np.ndarray
    tti: np.ndarray
    wsv0: np.ndarray
    raz0: np.ndarray


def vectorized_primary_fire_behaviour_prediction(
    fuel_type_code,
    ffmc,
    bui,
    ws,
    wd_rad,
    gs,
    aspect_rad,
    pc,
    pdf,
    cc,
    gfl,
    cbh,
    cfl,
    fmc,
    isi,
    lat,
    lon,
    elv,
    dj,
    d0,
    sd,
    sh,
    hr,
    theta_rad,
    accel,
    buieff,
) -> FBPPrimaryOutput:
    """Calculate the eight primary FBP fields with one call per broadcast element.

    Parameters have the same meaning as ``vectorized_fire_behaviour_prediction`` below. This
    entry point avoids the second calculation needed by that all-output wrapper.
    """
    cfb, cfc, fd_code, hfi, raz, ros, sfc, tfc = _vectorized_fbp_primary(
        fuel_type_code,
        ffmc,
        bui,
        ws,
        wd_rad,
        gs,
        aspect_rad,
        pc,
        pdf,
        cc,
        gfl,
        cbh,
        cfl,
        fmc,
        isi,
        lat,
        lon,
        elv,
        dj,
        d0,
        sd,
        sh,
        hr,
        theta_rad,
        accel,
        buieff,
    )
    return FBPPrimaryOutput(
        cfb=cfb,
        cfc=cfc,
        fd_code=fd_code,
        hfi=hfi,
        raz=raz,
        ros=ros,
        sfc=sfc,
        tfc=tfc,
    )


def vectorized_fire_behaviour_prediction(
    fuel_type_code,
    ffmc,
    bui,
    ws,
    wd_rad,
    gs,
    aspect_rad,
    pc,
    pdf,
    cc,
    gfl,
    cbh,
    cfl,
    fmc,
    isi,
    lat,
    lon,
    elv,
    dj,
    d0,
    sd,
    sh,
    hr,
    theta_rad,
    accel,
    buieff,
) -> FBPOutput:
    """Vectorizes cffdrs's real _fire_behaviour_prediction as-is - the exact private,
    vectorization-ready function fire_behaviour_prediction(input, "All") itself delegates to,
    jit-cloned via the same clone-and-patch chain as every other composite function in this
    module (see module docstring), not a re-derivation of its logic. Returns every field it
    computes (Primary + Secondary + wsv0/raz0) as one FBPOutput, same shape as the underlying
    function's own _FBPOutput - _vectorized_fbp_primary/_secondary above do the actual work,
    split in two only because a single guvectorize call can't fit all 70 input+output operands
    (see the comment above _FBP_PRIMARY_FIELDS).

    :param fuel_type_code: The Fire Behaviour Prediction fuel type code (see
        cffdrs.constants.FUEL_TYPE_CODES)
    :param ffmc: Fine Fuel Moisture Code
    :param bui: Buildup Index
    :param ws: Wind Speed (km/h)
    :param wd_rad: Wind direction, i.e. the compass bearing the wind is blowing from (radians)
    :param gs: Ground/terrain slope (%)
    :param aspect_rad: Aspect of the slope, i.e. the compass bearing the slope faces (radians)
    :param pc: Percent Conifer (%), only meaningful for the mixedwood fuel types M1/M2
    :param pdf: Percent Dead Balsam Fir (%), only meaningful for the mixedwood-dead fuel types
        M3/M4
    :param cc: Percent Cured Grass (%), only meaningful for the grass fuel types O1A/O1B
    :param gfl: Grass Fuel Load (kg/m^2)
    :param cbh: Crown Base Height (m), falls back to a fuel-type default (or, for C6, a value
        derived from sd/sh) when <= 0, > 50, or NaN; see cffdrs.crown_base_height
    :param cfl: Crown Fuel Load (kg/m^2), falls back to a fuel-type default when invalid; see
        cffdrs.crown_fuel_load
    :param fmc: Foliar Moisture Content (%), computed from lat/lon/elv/dj/d0 when <= 0, > 120,
        or NaN
    :param isi: Initial Spread Index, computed from ffmc and the net effective wind speed when
        <= 0
    :param lat: Latitude (decimal degrees), only used to compute fmc when fmc isn't supplied
    :param lon: Longitude (decimal degrees), only used to compute fmc when fmc isn't supplied
    :param elv: Elevation (m), only used to compute fmc when fmc isn't supplied
    :param dj: Day of year ("Julian date"), only used to compute fmc when fmc isn't supplied
    :param d0: Julian date of minimum foliar moisture content, only used to compute fmc when
        fmc isn't supplied
    :param sd: Stand density (stems/ha), only used for C6's crown base height fallback when cbh
        is invalid
    :param sh: Stand height (m), only used for C6's crown base height fallback when cbh is
        invalid
    :param hr: Hours since ignition, used for time-dependent (accel=1) rate of spread; negative
        values flip the sign of the returned cfb.
    :param theta_rad: Bearing of interest for the point rate of spread outputs tros/trost
        (radians)
    :param accel: 1 to use time-dependent (accelerating) rate of spread based on hr, 0 for
        equilibrium rate of spread
    :param buieff: 1 to apply the Buildup Effect to rate of spread (using bui), any other value
        disables it
    """
    primary = vectorized_primary_fire_behaviour_prediction(
        fuel_type_code,
        ffmc,
        bui,
        ws,
        wd_rad,
        gs,
        aspect_rad,
        pc,
        pdf,
        cc,
        gfl,
        cbh,
        cfl,
        fmc,
        isi,
        lat,
        lon,
        elv,
        dj,
        d0,
        sd,
        sh,
        hr,
        theta_rad,
        accel,
        buieff,
    )
    (
        be,
        sf,
        isi_out,
        ffmc_out,
        fmc_out,
        d0_out,
        rso,
        csi,
        fros,
        bros,
        hrost,
        frost,
        brost,
        fcfb,
        bcfb,
        ffi,
        bfi,
        ftfc,
        btfc,
        ti,
        fti,
        bti,
        lb,
        lbt,
        wsv,
        dh,
        db,
        df,
        tros,
        trost,
        tcfb,
        tfi,
        ttfc,
        tti,
        wsv0,
        raz0,
    ) = _vectorized_fbp_secondary(
        fuel_type_code,
        ffmc,
        bui,
        ws,
        wd_rad,
        gs,
        aspect_rad,
        pc,
        pdf,
        cc,
        gfl,
        cbh,
        cfl,
        fmc,
        isi,
        lat,
        lon,
        elv,
        dj,
        d0,
        sd,
        sh,
        hr,
        theta_rad,
        accel,
        buieff,
    )
    return FBPOutput(
        cfb=primary.cfb,
        cfc=primary.cfc,
        fd_code=primary.fd_code,
        hfi=primary.hfi,
        raz=primary.raz,
        ros=primary.ros,
        sfc=primary.sfc,
        tfc=primary.tfc,
        be=be,
        sf=sf,
        isi=isi_out,
        ffmc=ffmc_out,
        fmc=fmc_out,
        d0=d0_out,
        rso=rso,
        csi=csi,
        fros=fros,
        bros=bros,
        hrost=hrost,
        frost=frost,
        brost=brost,
        fcfb=fcfb,
        bcfb=bcfb,
        ffi=ffi,
        bfi=bfi,
        ftfc=ftfc,
        btfc=btfc,
        ti=ti,
        fti=fti,
        bti=bti,
        lb=lb,
        lbt=lbt,
        wsv=wsv,
        dh=dh,
        db=db,
        df=df,
        tros=tros,
        trost=trost,
        tcfb=tcfb,
        tfi=tfi,
        ttfc=ttfc,
        tti=tti,
        wsv0=wsv0,
        raz0=raz0,
    )
