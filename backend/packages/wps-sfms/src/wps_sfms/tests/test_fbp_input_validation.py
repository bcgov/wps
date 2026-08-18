import numpy as np
import pytest

from wps_sfms.fbp_input_validation import validate_percent_conifer


@pytest.mark.parametrize("percent_conifer", [np.nan, -1, 101])
def test_invalid_mixedwood_percent_conifer_fails(percent_conifer: float):
    fuel = np.array([[14]], dtype=np.float32)
    values = np.array([[percent_conifer]], dtype=np.float32)

    with pytest.raises(ValueError, match="missing or out-of-range"):
        validate_percent_conifer(fuel, values)


@pytest.mark.parametrize("percent_conifer", [0, 100])
def test_mixedwood_percent_conifer_accepts_range_boundaries(percent_conifer: float):
    fuel = np.array([[14]], dtype=np.float32)
    values = np.array([[percent_conifer]], dtype=np.float32)

    validate_percent_conifer(fuel, values)


def test_invalid_percent_conifer_is_ignored_outside_mixedwood():
    fuel = np.array([[1, 99, 102]], dtype=np.float32)
    values = np.array([[np.nan, -1, 101]], dtype=np.float32)

    validate_percent_conifer(fuel, values)
