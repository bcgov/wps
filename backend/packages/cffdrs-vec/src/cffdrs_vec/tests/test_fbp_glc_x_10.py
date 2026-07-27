"""
Validates cffdrs_vec.fbp (and cffdrs_vec.fwi.vectorized_isi) against the 20 published FBP System
test cases from GLC-X-10 (Wotton et al. 2009), Table 4 (inputs) and Table 5 (primary outputs).
See https://github.com/bcgov/wps/issues/4893.

The input/output CSVs (see _glc_x_10_data.py for exact provenance) are the R cffdrs package's own
digitized transcription of the paper's Tables 4/5, copied here by way of cffdrs_py's own copy of
those same files - not included in the installed cffdrs_py package, so vendored here rather than
depended on at runtime.
test_fbp_glc_x_10_rasters.py runs the same cases and the same calculate_primary_output()
(shared via _glc_x_10_data.py) through GeoTIFF rasters instead, to prove the array pipeline also
works end-to-end through real raster I/O.

Rather than calling a single all-in-one function, this test composes the individual vectorized
functions cffdrs_vec.fbp exports (foliar_moisture_content, surface_fuel_consumption,
slope_adjustment, rate_of_spread_extended, total_fuel_consumption, fire_intensity) the same way
cffdrs's own cffdrs.fire_behaviour_prediction._fire_behaviour_prediction orchestrates them for
its Primary output, but over batched arrays covering all 20 cases at once rather than one case
at a time - this is what these functions are for.

Note: an earlier version of this test validated app.fire_behaviour.prediction's *scalar*
calculate_fire_behaviour_prediction_using_cffdrs instead, and needed to xfail 17 of the 20 cases
because that wrapper hardcodes ground slope to 0, doesn't accept a D0 override, and hardcodes
grass fuel load to 0.35. None of those gaps exist here: this test calls the underlying cffdrs
functions directly with every published input, and all 20 cases match Table 5 within floating
point/rounding noise.
"""

import numpy as np
import pytest

from cffdrs_vec.tests._glc_x_10_data import RPackageGLCX10Cases, calculate_primary_output


@pytest.fixture(scope="module")
def cases():
    return RPackageGLCX10Cases()


def test_fbp_glc_x_10_ros(cases):
    ros, _, _, _, _, _, _ = calculate_primary_output(cases)
    np.testing.assert_allclose(ros, cases.expected_ros, rtol=1e-3, err_msg="ROS")


def test_fbp_glc_x_10_hfi(cases):
    _, hfi, _, _, _, _, _ = calculate_primary_output(cases)
    np.testing.assert_allclose(hfi, cases.expected_hfi, rtol=1e-3, err_msg="HFI")


def test_fbp_glc_x_10_cfb(cases):
    _, _, cfb, _, _, _, _ = calculate_primary_output(cases)
    np.testing.assert_allclose(cfb, cases.expected_cfb, atol=1e-3, err_msg="CFB")


def test_fbp_glc_x_10_sfc(cases):
    _, _, _, sfc, _, _, _ = calculate_primary_output(cases)
    np.testing.assert_allclose(sfc, cases.expected_sfc, rtol=1e-3, err_msg="SFC")


def test_fbp_glc_x_10_tfc(cases):
    _, _, _, _, tfc, _, _ = calculate_primary_output(cases)
    np.testing.assert_allclose(tfc, cases.expected_tfc, rtol=1e-3, err_msg="TFC")


def test_fbp_glc_x_10_raz(cases):
    _, _, _, _, _, raz, _ = calculate_primary_output(cases)
    np.testing.assert_allclose(raz, cases.expected_raz, atol=0.1, err_msg="RAZ")


def test_fbp_glc_x_10_fire_type(cases):
    _, _, _, _, _, _, fire_type = calculate_primary_output(cases)
    assert list(fire_type) == cases.expected_fire_type
