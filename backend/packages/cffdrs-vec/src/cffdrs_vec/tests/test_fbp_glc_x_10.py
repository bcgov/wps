"""
Validates cffdrs_vec.fbp (and cffdrs_vec.fwi.vectorized_isi) against the 20 published FBP System
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
test_fbp_glc_x_10_rasters.py runs the same two sources and the same calculate_primary_output()
(shared via _glc_x_10_data.py) through GeoTIFF rasters instead, to prove the array pipeline also
works end-to-end through real raster I/O.

Rather than calling a single all-in-one function, this test composes the individual vectorized
functions cffdrs_vec.fbp exports (foliar_moisture_content, surface_fuel_consumption,
slope_adjustment, rate_of_spread_extended, total_fuel_consumption, fire_intensity) the same way
cffdrs's own cffdrs.fire_behaviour_prediction._fire_behaviour_prediction orchestrates them for
its Primary output, but over batched arrays covering all 20 cases at once rather than one case
at a time - this is what these functions are for.

ROS, HFI and CFB use a looser tolerance for "paper" than "r_package" (GLCX10Source.rtol_ros_hfi/
atol_cfb): cffdrs_vec (like the current R cffdrs package) is consistently ~0.3-0.6% off the
paper's own published values for these three outputs specifically, while SFC/TFC/RAZ/fire type
match tightly for both sources. That's consistent with refinements made to the FBP
rate-of-spread/CFB equations in the years since this 2009 paper was published. cffdrs_vec was
already cross-checked against the current cffdrs package itself via hypothesis fuzz testing
(test_fbp_hypothesis.py), so the goal here is catching gross regressions against the paper, not
bit-for-bit reproduction of a since-superseded formula.

Note: an earlier version of this test validated app.fire_behaviour.prediction's *scalar*
calculate_fire_behaviour_prediction_using_cffdrs instead, and needed to xfail 17 of the 20 cases
because that wrapper hardcodes ground slope to 0, doesn't accept a D0 override, and hardcodes
grass fuel load to 0.35. None of those gaps exist here: this test calls the underlying cffdrs
functions directly with every published input.
"""

import numpy as np
import pytest

from cffdrs_vec.tests._glc_x_10_data import GLC_X_10_SOURCES, calculate_primary_output


@pytest.mark.parametrize("source", GLC_X_10_SOURCES, ids=lambda s: s.name)
def test_fbp_glc_x_10(source):
    inputs, expected = source.load()
    ros, hfi, cfb, sfc, tfc, raz, fire_type = calculate_primary_output(inputs)

    np.testing.assert_allclose(ros, expected.ros, rtol=source.rtol_ros_hfi, err_msg="ROS")
    np.testing.assert_allclose(hfi, expected.hfi, rtol=source.rtol_ros_hfi, err_msg="HFI")
    np.testing.assert_allclose(cfb, expected.cfb, atol=source.atol_cfb, err_msg="CFB")
    np.testing.assert_allclose(sfc, expected.sfc, rtol=1e-3, err_msg="SFC")
    np.testing.assert_allclose(tfc, expected.tfc, rtol=1e-3, err_msg="TFC")
    np.testing.assert_allclose(raz, expected.raz, atol=0.1, err_msg="RAZ")
    assert list(fire_type) == expected.fire_type
