import numpy as np
from numpy.testing import assert_allclose

from hypothesis import given, strategies as st, settings
import hypothesis.extra.numpy as hnp


from wps_sfms.interpolation.source import LAPSE_RATE, StationTemperatureSource


def test_zero_elevation_identity():
    temps = np.array([-5.0, 0.0, 12.3], dtype=np.float32)
    elevs = np.zeros_like(temps)
    out = StationTemperatureSource.compute_sea_level_temps(temps, elevs, LAPSE_RATE)
    assert_allclose(out, temps, atol=0)

    # round-trip with actual temps:
    rt = StationTemperatureSource.compute_actual_temps(out, elevs, LAPSE_RATE)
    assert_allclose(rt, temps, atol=0)


def test_positive_elevation_cools_when_applying_to_terrain():
    sea = np.array([20.0, 15.0, 10.0], dtype=np.float32)
    elev = np.array([1000.0, 1500.0, 2000.0], dtype=np.float32)
    out = StationTemperatureSource.compute_actual_temps(sea, elev, LAPSE_RATE)
    assert np.all(out < sea)


def test_negative_elevation_warms_when_applying_to_terrain():
    sea = np.array([10.0], dtype=np.float32)
    elev = np.array([-100.0], dtype=np.float32)
    out = StationTemperatureSource.compute_actual_temps(sea, elev, LAPSE_RATE)
    assert out[0] > sea[0]


def test_broadcasting_shapes():
    # sea: (2,1), elev: (3,) => result (2,3)
    temps = np.array([[20.0], [15.0]], dtype=np.float32)
    elevs = np.array([0.0, 1000.0, 2000.0], dtype=np.float32)
    out = StationTemperatureSource.compute_actual_temps(temps, elevs, LAPSE_RATE)
    expected = temps - elevs * np.float32(LAPSE_RATE)
    assert_allclose(out, expected, atol=1e-6)
    assert out.shape == (2, 3)
    assert out.dtype == np.float32


def test_dtype_is_float32_even_if_inputs_float64():
    temps = np.array([20.0, 10.0], dtype=np.float64)
    elevs = np.array([0.0, 1000.0], dtype=np.float64)

    sea = StationTemperatureSource.compute_sea_level_temps(temps, elevs, LAPSE_RATE)
    assert sea.dtype == np.float32

    act = StationTemperatureSource.compute_actual_temps(sea, elevs.astype(np.float32), LAPSE_RATE)
    assert act.dtype == np.float32


def test_round_trip_sea_then_actual_returns_original():
    # compute_actual(compute_sea(temps, elev), elev) == temps
    temps = np.array([5.0, 10.0, -3.0, 0.0], dtype=np.float32)
    elevs = np.array([0.0, 100.0, 500.0, 2000.0], dtype=np.float32)
    sea = StationTemperatureSource.compute_sea_level_temps(temps, elevs, LAPSE_RATE)
    back = StationTemperatureSource.compute_actual_temps(sea, elevs, LAPSE_RATE)
    assert_allclose(back, temps, rtol=0, atol=1e-6)


# ---------------------------
# Hypothesis property tests
# ---------------------------

# Reasonable float32 ranges to avoid inf/overflow for products (lapse_rate * elevation)
finite_float32 = st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6)

finite_temp_c = st.floats(
    allow_nan=False,
    allow_infinity=False,
    min_value=-100.0,
    max_value=70.0,  # practical Earth temps
)

finite_elev_m = st.floats(
    allow_nan=False,
    allow_infinity=False,
    min_value=-500.0,
    max_value=9000.0,  # from Dead Sea to high mountains
)

finite_lapse = st.floats(
    allow_nan=False,
    allow_infinity=False,
    min_value=1e-6,
    max_value=0.02,  # 0.0065 is typical; keep positive
)


@given(
    temps=hnp.arrays(
        np.float32,
        shape=hnp.array_shapes(min_dims=1, max_dims=1, min_side=1, max_side=200),
        elements=finite_temp_c,
    ),
    elevs=hnp.arrays(
        np.float32,
        shape=hnp.array_shapes(min_dims=1, max_dims=1, min_side=1, max_side=200),
        elements=finite_elev_m,
    ),
    lapse=finite_lapse,
)
@settings(deadline=None, max_examples=200)
def test_round_trip_property(temps, elevs, lapse):
    # Align lengths by truncation for simplicity
    n = min(len(temps), len(elevs))
    temps = temps[:n].astype(np.float32, copy=False)
    elevs = elevs[:n].astype(np.float32, copy=False)

    sea = StationTemperatureSource.compute_sea_level_temps(temps, elevs, lapse)
    back = StationTemperatureSource.compute_actual_temps(sea, elevs, lapse)
    assert_allclose(back, temps, atol=1e-4)


@given(
    sea=hnp.arrays(
        np.float32,
        shape=hnp.array_shapes(min_dims=1, max_dims=1, min_side=1, max_side=200),
        elements=finite_temp_c,
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

    out = StationTemperatureSource.compute_actual_temps(sea, elev, lapse)
    # For strictly positive lapse & non-negative elevation:
    assert np.all(out <= sea + 1e-6)


@given(
    sea=hnp.arrays(
        np.float32,
        shape=hnp.array_shapes(min_dims=1, max_dims=1, min_side=1, max_side=200),
        elements=finite_temp_c,
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

    out = StationTemperatureSource.compute_actual_temps(sea, elev, lapse)
    assert np.all(out >= sea - 1e-6)


@given(
    temps=hnp.arrays(np.float32, shape=(10, 1), elements=finite_temp_c),
    elevs=hnp.arrays(np.float32, shape=(15,), elements=finite_elev_m),
    lapse=finite_lapse,
)
@settings(deadline=None, max_examples=100)
def test_broadcasting_with_hypothesis(temps, elevs, lapse):
    out = StationTemperatureSource.compute_actual_temps(temps, elevs, lapse)
    expected = temps - elevs * np.float32(lapse)
    assert out.shape == (10, 15)
    assert out.dtype == np.float32
    assert_allclose(out, expected, atol=1e-5)
