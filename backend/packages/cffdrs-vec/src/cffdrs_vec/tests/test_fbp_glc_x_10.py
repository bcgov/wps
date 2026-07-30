"""
Validates cffdrs_vec.fbp.vectorized_fire_behaviour_prediction against the 20 published FBP System
test cases from GLC-X-10 (Wotton et al. 2009), Table 4 (inputs) and Table 5 (primary outputs).
See https://github.com/bcgov/wps/issues/4893.

Parametrized over two independent data sources (see _glc_x_10_data.py's GLCX10Source for exact
provenance of each):
- "r_package": the R cffdrs package's own digitized transcription of the paper's Tables 4/5,
  vendored here by way of cffdrs_py's own copy of those same files.
- "paper": transcribed independently, straight from the published PDF via `pdftotext -layout`,
  with no R package in the chain at all.
If these two ever disagree, the R-sourced CSVs and the paper have actually diverged and that's
worth investigating; both staying green is the cross-validation working as intended.
test_fbp_glc_x_10_rasters.py runs the same two sources through GeoTIFF rasters instead, to prove
the array pipeline also works end-to-end through real raster I/O.

ROS, HFI and CFB use a looser tolerance for "paper" than "r_package" (GLCX10Source.rtol_ros_hfi/
atol_cfb): cffdrs_vec (like the current R cffdrs package) is consistently ~0.3-0.6% off the
paper's own published values for these three outputs specifically, while SFC/TFC/RAZ/fire type
match tightly for both sources. That's consistent with refinements made to the FBP
rate-of-spread/CFB equations in the years since this 2009 paper was published.
vectorized_fire_behaviour_prediction was already cross-checked against cffdrs's own
fire_behaviour_prediction() directly (test_fbp_e2e_vectorized.py), so the goal here is catching
gross regressions against the paper, not bit-for-bit reproduction of a since-superseded formula.
"""

import numpy as np
import pytest

from cffdrs_vec import fbp
from cffdrs_vec.tests._glc_x_10_data import FIRE_TYPE_BY_FD_CODE_INT, GLC_X_10_SOURCES


@pytest.mark.parametrize("source", GLC_X_10_SOURCES, ids=lambda s: s.name)
def test_fbp_glc_x_10(source):
    inputs, expected = source.load()
    shape = inputs.fuel_type_codes.shape
    zeros = np.zeros(shape)
    int_zeros = np.zeros(shape, dtype=np.int64)

    result = fbp.vectorized_fire_behaviour_prediction(
        inputs.fuel_type_codes,
        inputs.ffmc,
        inputs.bui,
        inputs.ws,
        inputs.wd_rad,
        inputs.gs,
        inputs.aspect_rad,
        inputs.pc,
        inputs.pdf,
        inputs.cc,
        inputs.gfl,
        inputs.cbh,
        inputs.cfl,
        zeros,  # fmc - all 20 published cases leave it unset, so it's always derived internally
        zeros,  # isi - all 20 published cases leave it unset, so it's always derived internally
        inputs.lat,
        inputs.lon,
        inputs.elv,
        inputs.dj,
        inputs.d0,
        zeros,  # sd - no stand density data in GLC-X-10
        zeros,  # sh - no stand height data in GLC-X-10
        np.ones(shape),  # hr
        zeros,  # theta_rad - unused by Primary output
        int_zeros,  # accel
        np.ones(shape, dtype=np.int64),  # buieff - use raw BUI, not effective BUI
    )

    np.testing.assert_allclose(result.ros, expected.ros, rtol=source.rtol_ros_hfi, err_msg="ROS")
    np.testing.assert_allclose(result.hfi, expected.hfi, rtol=source.rtol_ros_hfi, err_msg="HFI")
    np.testing.assert_allclose(result.cfb, expected.cfb, atol=source.atol_cfb, err_msg="CFB")
    np.testing.assert_allclose(result.sfc, expected.sfc, rtol=1e-3, err_msg="SFC")
    np.testing.assert_allclose(result.tfc, expected.tfc, rtol=1e-3, err_msg="TFC")
    np.testing.assert_allclose(result.raz, expected.raz, atol=0.1, err_msg="RAZ")
    fire_type = [FIRE_TYPE_BY_FD_CODE_INT[c] for c in result.fd_code]
    assert fire_type == expected.fire_type
