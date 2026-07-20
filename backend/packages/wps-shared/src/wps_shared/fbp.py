"""Raster-friendly (vectorized) wrapper around the scalar CFFDRS FBP System calculation.

Unlike the FWI functions in `fwi.py`, the FBP calculation branches on a categorical fuel
type string and recurses (e.g. M1/M2/M3/M4 blend rate of spread from other fuel types).
Neither is supported by `numba.vectorize`: nopython mode can't type the recursive call,
and object mode still requires every argument's dtype to be numpy-representable, which
rules out string arrays. `numpy.vectorize` is used instead - it gives the same
elementwise-over-arrays interface (including broadcasting over 2D raster arrays), at the
cost of a Python-level loop per pixel rather than a compiled ufunc.
"""

import numpy as np
from cffdrs.fire_behaviour_prediction import fire_behaviour_prediction
from cffdrs.models import FBPInput

# FBPPrimaryOutput.fd is a single letter (surface/intermittent crown/continuous crown).
# Encoded as an integer so vectorized_fbp_primary can return a fully numeric tuple.
FIRE_DESCRIPTION_CODES = {"S": 0, "I": 1, "C": 2}
FIRE_DESCRIPTION_BY_CODE = {code: letter for letter, code in FIRE_DESCRIPTION_CODES.items()}


def fbp_primary(
    fuel_type: str,
    ffmc: float,
    bui: float,
    ws: float,
    wd: float,
    gs: float,
    aspect: float,
    lat: float,
    lon: float,
    elv: float,
    dj: float,
    d0: float,
    pc: float,
    pdf: float,
    cc: float,
    gfl: float,
):
    """Runs the FBP System calculation chain for a single point and returns its Primary
    outputs (ROS, CFB, SFC, CFC, TFC, HFI, RAZ, FD) as a plain numeric tuple.

    NaN may be passed for any of pc, pdf, cc, gfl, d0, or elv to fall back to the
    fuel-type-specific default that `FBPInput` and the calculation chain apply internally
    (this mirrors GLC-X-10 Table 4, where a "-" cell means "use the system default", except
    for d0 where it means "derive D0 from the foliar moisture content equations").
    """
    fbp_input = FBPInput(
        fuel_type=fuel_type,
        ffmc=ffmc,
        bui=bui,
        ws=ws,
        wd=wd,
        gs=gs,
        aspect=aspect,
        lat=lat,
        lon=lon,
        elv=elv,
        dj=dj,
        d0=d0,
        pc=pc,
        pdf=pdf,
        cc=cc,
        gfl=gfl,
    )
    result = fire_behaviour_prediction(fbp_input, "Primary")
    return (
        result.ros,
        result.cfb,
        result.sfc,
        result.cfc,
        result.tfc,
        result.hfi,
        result.raz,
        FIRE_DESCRIPTION_CODES[result.fd] if result.fd else -1,
    )


vectorized_fbp_primary = np.vectorize(
    fbp_primary,
    otypes=[float, float, float, float, float, float, float, int],
)
