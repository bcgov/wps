import numpy as np
import pytest

from wps_sfms.fbp_input_validation import validate_percent_conifer

MIXEDWOOD = np.array([[True]])


@pytest.mark.parametrize("percent_conifer", [np.nan, -1, 101])
def test_invalid_mixedwood_percent_conifer_fails(percent_conifer: float):
    values = np.array([[percent_conifer]], dtype=np.float32)

    with pytest.raises(ValueError, match="missing or out-of-range"):
        validate_percent_conifer(values, MIXEDWOOD)


@pytest.mark.parametrize("percent_conifer", [0, 100])
def test_mixedwood_percent_conifer_accepts_range_boundaries(percent_conifer: float):
    values = np.array([[percent_conifer]], dtype=np.float32)

    validate_percent_conifer(values, MIXEDWOOD)


def test_invalid_percent_conifer_is_ignored_outside_mixedwood():
    values = np.array([[np.nan, -1, 101]], dtype=np.float32)

    validate_percent_conifer(values, np.array([[False, False, False]]))
