"""
Validates cffdrs_vec.fbp.vectorized_fire_behaviour_prediction - a jit-cloned vectorization of
cffdrs's own, real _fire_behaviour_prediction (see fbp.py's module docstring for the clone-and-
patch technique) - against cffdrs's public fire_behaviour_prediction() (output="All" plus the
WSV0/RAZ0 shortcuts for the 2 fields that aren't part of Primary/Secondary/All), over the 20
published GLC-X-10 (Wotton et al. 2009) cases. See https://github.com/bcgov/wps/issues/4893.

This checks a literal vectorization of _fire_behaviour_prediction itself - a mismatch here points
at the jit-clone machinery in fbp.py (a missed patch, a wrong clone) rather than at a
reimplementation of cffdrs's own logic.

All 44 FBPOutput fields are checked - see fbp.py's module docstring for why
vectorized_fire_behaviour_prediction is internally two guvectorize calls merged into one (a
single guvectorize call can't have more than 64 total input+output operands).

Tight tolerance throughout: both sides run the exact same current formula.
"""

import numpy as np
import pytest
from cffdrs.constants import FUEL_TYPE_CODES
from cffdrs.fire_behaviour_prediction import fire_behaviour_prediction

from cffdrs_vec.fbp import FBPOutput, vectorized_fire_behaviour_prediction
from cffdrs_vec.tests._glc_x_10_data import GLC_X_10_SOURCES

# fire_behaviour_prediction()'s public "All" output represents Fire Type as a string ("S"/"I"/"C"),
# while _FBPOutput.fd_code (what vectorized_fire_behaviour_prediction returns) is the same value
# as an int - GLC-X-10 has no NF/WA fuel-type case, so fd is never None here.
_FD_CODE_BY_STRING = {"S": 0, "I": 1, "C": 2}


@pytest.mark.parametrize("source", GLC_X_10_SOURCES, ids=lambda s: s.name)
def test_vectorized_fire_behaviour_prediction_matches_fire_behaviour_prediction(source):
    # Built from the same already-clamped/radians-converted FBPInput fields
    # _fire_behaviour_prediction itself expects (see its docstring) - to_fbp_inputs() runs each
    # case through FBPInput.__post_init__ once, same as a real caller would.
    fbp_inputs = source.to_fbp_inputs()

    fuel_type_codes = np.array([FUEL_TYPE_CODES[i.fuel_type] for i in fbp_inputs], dtype=np.int64)
    ffmc = np.array([i.ffmc for i in fbp_inputs])
    bui = np.array([i.bui for i in fbp_inputs])
    ws = np.array([i.ws for i in fbp_inputs])
    wd_rad = np.array([i.wd for i in fbp_inputs])
    gs = np.array([i.gs for i in fbp_inputs])
    aspect_rad = np.array([i.aspect for i in fbp_inputs])
    pc = np.array([i.pc for i in fbp_inputs])
    pdf = np.array([i.pdf for i in fbp_inputs])
    cc = np.array([i.cc for i in fbp_inputs])
    gfl = np.array([i.gfl for i in fbp_inputs])
    cbh = np.array([i.cbh for i in fbp_inputs])
    cfl = np.array([i.cfl for i in fbp_inputs])
    fmc = np.array([i.fmc for i in fbp_inputs])
    isi = np.array([i.isi for i in fbp_inputs])
    lat = np.array([i.lat for i in fbp_inputs])
    lon = np.array([i.lon for i in fbp_inputs])
    elv = np.array([i.elv for i in fbp_inputs])
    dj = np.array([i.dj for i in fbp_inputs])
    d0 = np.array([i.d0 for i in fbp_inputs])
    sd = np.array([i.sd for i in fbp_inputs])
    sh = np.array([i.sh for i in fbp_inputs])
    hr = np.array([i.hr for i in fbp_inputs])
    theta_rad = np.array([i.theta for i in fbp_inputs])
    accel = np.array([i.accel for i in fbp_inputs], dtype=np.int64)
    buieff = np.array([i.bui_eff for i in fbp_inputs], dtype=np.int64)

    result = vectorized_fire_behaviour_prediction(
        fuel_type_codes,
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

    all_output = [fire_behaviour_prediction(i, output="All") for i in fbp_inputs]
    wsv0 = np.array([fire_behaviour_prediction(i, output="WSV0") for i in fbp_inputs])
    raz0 = np.array([fire_behaviour_prediction(i, output="RAZ0") for i in fbp_inputs])

    for field in FBPOutput._fields:
        if field == "wsv0":
            reference = wsv0
        elif field == "raz0":
            reference = raz0
        elif field == "fd_code":
            reference = np.array([_FD_CODE_BY_STRING[r.fd] for r in all_output])
        else:
            reference = np.array([getattr(r, field) for r in all_output])
        np.testing.assert_allclose(
            getattr(result, field), reference, rtol=1e-9, atol=1e-9, err_msg=field
        )
