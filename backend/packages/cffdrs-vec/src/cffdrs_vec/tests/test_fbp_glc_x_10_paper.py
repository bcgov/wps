"""
Validates cffdrs_vec.fbp against the 20 published FBP System test cases from GLC-X-10 (Wotton et
al. 2009), Tables 4 (inputs) and 5 (primary outputs) - transcribed directly from the PDF via
`pdftotext -layout`, independent of the R-cffdrs-sourced CSVs test_fbp_glc_x_10.py uses. See
_glc_x_10_data.py for exact provenance and how the two overlapping-text cells in the PDF were
resolved, and https://github.com/bcgov/wps/issues/4893.

Structurally identical to test_fbp_glc_x_10.py (same calculate_primary_output composition) - the
point of this file is the independent data source, not a different code path. If this ever
disagrees with test_fbp_glc_x_10.py's results, the R-sourced CSVs and the paper have actually
diverged and that's worth investigating; if both stay green together, that's the cross-validation
working as intended.

ROS, HFI and CFB use looser tolerances than test_fbp_glc_x_10.py's: cffdrs_vec (like the current R
cffdrs package) is consistently ~0.3-0.6% off the paper's own published values for these three
outputs specifically, while SFC/TFC/RAZ/fire type match to within the same tight tolerance used
elsewhere. That's consistent with refinements made to the FBP rate-of-spread/CFB equations in the
years since this 2009 paper was published, not a defect in this port - cffdrs_vec was already
cross-checked against the current cffdrs package itself via hypothesis fuzz testing
(test_fbp_hypothesis.py), so the goal here is catching gross regressions against the paper, not
bit-for-bit reproduction of a since-superseded formula.
"""

import numpy as np
import pytest

from cffdrs_vec.tests._glc_x_10_data import GLCX10PaperCases, calculate_primary_output


@pytest.fixture(scope="module")
def cases():
    return GLCX10PaperCases()


def test_fbp_glc_x_10_paper_ros(cases):
    ros, _, _, _, _, _, _ = calculate_primary_output(cases)
    np.testing.assert_allclose(ros, cases.expected_ros, rtol=1e-2, err_msg="ROS")


def test_fbp_glc_x_10_paper_hfi(cases):
    _, hfi, _, _, _, _, _ = calculate_primary_output(cases)
    np.testing.assert_allclose(hfi, cases.expected_hfi, rtol=1e-2, err_msg="HFI")


def test_fbp_glc_x_10_paper_cfb(cases):
    _, _, cfb, _, _, _, _ = calculate_primary_output(cases)
    np.testing.assert_allclose(cfb, cases.expected_cfb, atol=3e-3, err_msg="CFB")


def test_fbp_glc_x_10_paper_sfc(cases):
    _, _, _, sfc, _, _, _ = calculate_primary_output(cases)
    np.testing.assert_allclose(sfc, cases.expected_sfc, rtol=1e-3, err_msg="SFC")


def test_fbp_glc_x_10_paper_tfc(cases):
    _, _, _, _, tfc, _, _ = calculate_primary_output(cases)
    np.testing.assert_allclose(tfc, cases.expected_tfc, rtol=1e-3, err_msg="TFC")


def test_fbp_glc_x_10_paper_raz(cases):
    _, _, _, _, _, raz, _ = calculate_primary_output(cases)
    np.testing.assert_allclose(raz, cases.expected_raz, atol=0.1, err_msg="RAZ")


def test_fbp_glc_x_10_paper_fire_type(cases):
    _, _, _, _, _, _, fire_type = calculate_primary_output(cases)
    assert list(fire_type) == cases.expected_fire_type
