"""
Differential property tests for cffdrs_vec.fwi: for every exposed vectorized_* function, check
that calling it on a single-element array gives the same result as calling the plain, unjitted
cffdrs reference function with the same scalar inputs, across the input space rather than just a
handful of fixed examples.

deadline=None on every test: the first hypothesis example triggers numba's (comparatively slow)
JIT compilation of the vectorized function; subsequent examples reuse the compiled dispatcher and
are fast, but hypothesis's default per-example deadline would otherwise flag that first one.
"""

import cffdrs
import numpy as np
from cffdrs_vec import fwi
from hypothesis import given, settings
from hypothesis import strategies as st

ffmc = st.floats(0.0, 101.0, allow_nan=False)
dmc = st.floats(0.0, 500.0, allow_nan=False)
dc = st.floats(0.0, 1000.0, allow_nan=False)
bui = st.floats(0.0, 300.0, allow_nan=False)
isi = st.floats(0.0, 300.0, allow_nan=False)
temp = st.floats(-40.0, 45.0, allow_nan=False)
rh = st.floats(0.0, 100.0, allow_nan=False)
precip = st.floats(0.0, 300.0, allow_nan=False)
wind_speed = st.floats(0.0, 150.0, allow_nan=False)
lat = st.floats(-90.0, 90.0, allow_nan=False)
month = st.integers(1, 12)
lat_adjust = st.booleans()
fbp_mod = st.booleans()


@given(dmc=dmc, dc=dc)
@settings(deadline=None, max_examples=200)
def test_vectorized_bui_matches_reference(dmc, dc):
    actual = fwi.vectorized_bui(np.array([dmc]), np.array([dc]))[0]
    expected = cffdrs.buildup_index(dmc, dc)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)


@given(dc=dc, temp=temp, rh=rh, precip=precip, lat=lat, month=month, lat_adjust=lat_adjust)
@settings(deadline=None, max_examples=200)
def test_vectorized_dc_matches_reference(dc, temp, rh, precip, lat, month, lat_adjust):
    actual = fwi.vectorized_dc(
        np.array([dc]),
        np.array([temp]),
        np.array([rh]),
        np.array([precip]),
        np.array([lat]),
        np.array([month]),
        lat_adjust,
    )[0]
    expected = cffdrs.drought_code(dc, temp, rh, precip, lat, month, lat_adjust)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)


@given(dmc=dmc, temp=temp, rh=rh, precip=precip, lat=lat, month=month, lat_adjust=lat_adjust)
@settings(deadline=None, max_examples=200)
def test_vectorized_dmc_matches_reference(dmc, temp, rh, precip, lat, month, lat_adjust):
    actual = fwi.vectorized_dmc(
        np.array([dmc]),
        np.array([temp]),
        np.array([rh]),
        np.array([precip]),
        np.array([lat]),
        np.array([month]),
        lat_adjust,
    )[0]
    expected = cffdrs.duff_moisture_code(dmc, temp, rh, precip, lat, month, lat_adjust)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)


@given(ffmc=ffmc, temp=temp, rh=rh, wind_speed=wind_speed, precip=precip)
@settings(deadline=None, max_examples=200)
def test_vectorized_ffmc_matches_reference(ffmc, temp, rh, wind_speed, precip):
    actual = fwi.vectorized_ffmc(
        np.array([ffmc]), np.array([temp]), np.array([rh]), np.array([wind_speed]), np.array([precip])
    )[0]
    expected = cffdrs.fine_fuel_moisture_code(ffmc, temp, rh, wind_speed, precip)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)


@given(ffmc=ffmc, wind_speed=wind_speed, fbp_mod=fbp_mod)
@settings(deadline=None, max_examples=200)
def test_vectorized_isi_matches_reference(ffmc, wind_speed, fbp_mod):
    actual = fwi.vectorized_isi(np.array([ffmc]), np.array([wind_speed]), fbp_mod)[0]
    expected = cffdrs.initial_spread_index(ffmc, wind_speed, fbp_mod)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)


@given(isi=isi, bui=bui)
@settings(deadline=None, max_examples=200)
def test_vectorized_fwi_matches_reference(isi, bui):
    actual = fwi.vectorized_fwi(np.array([isi]), np.array([bui]))[0]
    expected = cffdrs.fire_weather_index(isi, bui)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)
