"""
Hypothesis property tests for LapseRateAdjustedSource lapse-rate math.
"""

import numpy as np
from numpy.testing import assert_allclose

from hypothesis import given, strategies as st, settings
import hypothesis.extra.numpy as hnp

from wps_sfms.interpolation.source import LAPSE_RATE, LapseRateAdjustedSource


finite_value_c = st.floats(
    allow_nan=False,
    allow_infinity=False,
    min_value=-100.0,
    max_value=70.0,
)

finite_elev_m = st.floats(
    allow_nan=False,
    allow_infinity=False,
    min_value=-500.0,
    max_value=9000.0,
)

finite_lapse = st.floats(
    allow_nan=False,
    allow_infinity=False,
    min_value=1e-6,
    max_value=LAPSE_RATE,
)


@given(
    values=hnp.arrays(
        np.float32,
        shape=hnp.array_shapes(min_dims=1, max_dims=1, min_side=1, max_side=200),
        elements=finite_value_c,
    ),
    elevs=hnp.arrays(
        np.float32,
        shape=hnp.array_shapes(min_dims=1, max_dims=1, min_side=1, max_side=200),
        elements=finite_elev_m,
    ),
    lapse=finite_lapse,
)
@settings(deadline=None, max_examples=200)
def test_round_trip_property(values, elevs, lapse):
    n = min(len(values), len(elevs))
    values = values[:n].astype(np.float32, copy=False)
    elevs = elevs[:n].astype(np.float32, copy=False)

    sea = LapseRateAdjustedSource.compute_sea_level_values(values, elevs, lapse)
    back = LapseRateAdjustedSource.compute_adjusted_values(sea, elevs, lapse)
    assert_allclose(back, values, atol=1e-4)


@given(
    sea=hnp.arrays(
        np.float32,
        shape=hnp.array_shapes(min_dims=1, max_dims=1, min_side=1, max_side=200),
        elements=finite_value_c,
    ),
    elev=hnp.arrays(
        np.float32,
        shape=hnp.array_shapes(min_dims=1, max_dims=1, min_side=1, max_side=200),
        elements=st.floats(min_value=0.0, max_value=9000.0, allow_nan=False, allow_infinity=False),
    ),
    lapse=finite_lapse,
)
@settings(deadline=None, max_examples=200)
def test_monotone_cooling_with_positive_elevation(sea, elev, lapse):
    n = min(len(sea), len(elev))
    sea = sea[:n]
    elev = elev[:n]

    out = LapseRateAdjustedSource.compute_adjusted_values(sea, elev, lapse)
    assert np.all(out <= sea + 1e-6)


@given(
    sea=hnp.arrays(
        np.float32,
        shape=hnp.array_shapes(min_dims=1, max_dims=1, min_side=1, max_side=200),
        elements=finite_value_c,
    ),
    elev=hnp.arrays(
        np.float32,
        shape=hnp.array_shapes(min_dims=1, max_dims=1, min_side=1, max_side=200),
        elements=st.floats(max_value=0.0, min_value=-500.0, allow_nan=False, allow_infinity=False),
    ),
    lapse=finite_lapse,
)
@settings(deadline=None, max_examples=200)
def test_negative_elevation_warms(sea, elev, lapse):
    n = min(len(sea), len(elev))
    sea = sea[:n]
    elev = elev[:n]

    out = LapseRateAdjustedSource.compute_adjusted_values(sea, elev, lapse)
    assert np.all(out >= sea - 1e-6)
