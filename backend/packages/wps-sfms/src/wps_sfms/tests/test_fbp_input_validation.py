import numpy as np
import pytest

from wps_sfms.fbp_input_validation import validate_grass_curing, validate_percent_conifer

MIXEDWOOD = np.array([[True]])


@pytest.mark.parametrize("percent_conifer", [np.nan, -1, 101])
def test_invalid_mixedwood_percent_conifer_fails(percent_conifer: float):
    values = np.array([[percent_conifer]], dtype=np.float32)

    with pytest.raises(ValueError, match="missing or out-of-range"):
        validate_percent_conifer(percent_conifer=values, mixedwood_mask=MIXEDWOOD)


@pytest.mark.parametrize("percent_conifer", [0, 100])
def test_mixedwood_percent_conifer_accepts_range_boundaries(percent_conifer: float):
    values = np.array([[percent_conifer]], dtype=np.float32)

    validate_percent_conifer(percent_conifer=values, mixedwood_mask=MIXEDWOOD)


def test_invalid_percent_conifer_is_ignored_outside_mixedwood():
    values = np.array([[np.nan, -1, 101]], dtype=np.float32)

    validate_percent_conifer(
        percent_conifer=values, mixedwood_mask=np.array([[False, False, False]])
    )


@pytest.mark.parametrize("grass_curing", [np.nan, -1, 101])
def test_invalid_grass_curing_on_grass_fails(grass_curing: float):
    values = np.array([[grass_curing]], dtype=np.float32)
    grass_mask = np.array([[True]])

    with pytest.raises(ValueError, match="grass pixels"):
        validate_grass_curing(grass_curing=values, grass_mask=grass_mask)


def test_invalid_grass_curing_is_ignored_outside_grass():
    validate_grass_curing(
        grass_curing=np.array([[np.nan, -1, 101]], dtype=np.float32),
        grass_mask=np.array([[False, False, False]]),
    )
