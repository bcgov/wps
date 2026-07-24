"""
Differential property tests for cffdrs_vec.fbp: for every exposed vectorized_* function, check
that calling it on a single-element array gives the same result as calling the plain, unjitted
cffdrs reference function (the public, string-based fuel-type API) with the same scalar inputs,
across the input space rather than just a handful of fixed examples.

fuel_type is fuzzed by sampling real cffdrs fuel type names (including NF/WA, the non-fuel and
unknown codes) rather than random ints, so the different fuel-type branches (M1-M4 blends,
O1A/O1B grass curing, C6's separate crown/surface split, NF/WA short-circuits) all actually get
exercised - a raw int strategy would mostly land on values with no meaning at all.

deadline=None on every test: the first hypothesis example triggers numba's (comparatively slow)
JIT compilation of the vectorized function; subsequent examples reuse the compiled dispatcher and
are fast, but hypothesis's default per-example deadline would otherwise flag that first one.
"""

import math

import cffdrs.back_rate_of_spread
import cffdrs.c6_calc
import cffdrs.cfb_calc
import cffdrs.distance_at_time
import cffdrs.fire_intensity
import cffdrs.foliar_moisture_content
import cffdrs.length_to_breadth
import cffdrs.length_to_breadth_at_time
import cffdrs.rate_of_spread
import cffdrs.rate_of_spread_at_time
import cffdrs.slope_calc
import cffdrs.surface_fuel_consumption
import cffdrs.total_fuel_consumption
import numpy as np
from cffdrs.constants import FUEL_TYPE_CODES
from cffdrs_vec import fbp
from hypothesis import given, settings
from hypothesis import strategies as st

# (name, code) pairs, so fuel_type is fuzzed over every real cffdrs fuel type - including NF/WA -
# rather than arbitrary ints that would mostly land on nothing meaningful.
fuel_type = st.sampled_from(sorted(FUEL_TYPE_CODES.items()))

ffmc = st.floats(0.0, 101.0, allow_nan=False)
bui = st.floats(0.0, 300.0, allow_nan=False)
isi = st.floats(0.0, 300.0, allow_nan=False)
fmc = st.floats(0.0, 200.0, allow_nan=False)
sfc = st.floats(0.0, 30.0, allow_nan=False)
cbh = st.floats(0.0, 50.0, allow_nan=False)
cfl = st.floats(0.0, 5.0, allow_nan=False)
pc = st.floats(0.0, 100.0, allow_nan=False)
pdf = st.floats(0.0, 100.0, allow_nan=False)
cc = st.floats(0.0, 100.0, allow_nan=False)
gfl = st.floats(0.0, 5.0, allow_nan=False)
wind_speed = st.floats(0.0, 150.0, allow_nan=False)
lat = st.floats(-90.0, 90.0, allow_nan=False)
lon = st.floats(0.0, 180.0, allow_nan=False)
elv = st.floats(0.0, 4000.0, allow_nan=False)
day_of_year = st.integers(1, 365).map(float)
d0 = st.floats(0.0, 365.0, allow_nan=False)
hr = st.floats(0.0, 300.0, allow_nan=False)
cfb = st.floats(0.0, 1.0, allow_nan=False)
lb = st.floats(1.0, 20.0, allow_nan=False)
ros = st.floats(0.0, 200.0, allow_nan=False)
rso = st.floats(0.0, 200.0, allow_nan=False)
rsi = st.floats(0.0, 200.0, allow_nan=False)
rss = st.floats(0.0, 200.0, allow_nan=False)
rsc = st.floats(0.0, 200.0, allow_nan=False)
csi = st.floats(0.0, 5000.0, allow_nan=False)
fc = st.floats(0.0, 30.0, allow_nan=False)
angle_rad = st.floats(0.0, 2 * math.pi, allow_nan=False)
gs = st.floats(0.0, 100.0, allow_nan=False)


@given(fmc=fmc, cbh=cbh)
@settings(deadline=None, max_examples=200)
def test_vectorized_critical_surface_intensity_matches_reference(fmc, cbh):
    actual = fbp.vectorized_critical_surface_intensity(np.array([fmc]), np.array([cbh]))[0]
    expected = cffdrs.cfb_calc.critical_surface_intensity(fmc, cbh)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)


@given(ros=ros, rso=rso)
@settings(deadline=None, max_examples=200)
def test_vectorized_crown_fraction_burned_matches_reference(ros, rso):
    actual = fbp.vectorized_crown_fraction_burned(np.array([ros]), np.array([rso]))[0]
    expected = cffdrs.cfb_calc.crown_fraction_burned(ros, rso)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)


@given(isi=isi, fmc=fmc)
@settings(deadline=None, max_examples=200)
def test_vectorized_crown_rate_of_spread_c6_matches_reference(isi, fmc):
    actual = fbp.vectorized_crown_rate_of_spread_c6(np.array([isi]), np.array([fmc]))[0]
    expected = cffdrs.c6_calc.crown_rate_of_spread_c6(isi, fmc)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)


@given(isi=isi)
@settings(deadline=None, max_examples=200)
def test_vectorized_intermediate_surface_rate_of_spread_c6_matches_reference(isi):
    actual = fbp.vectorized_intermediate_surface_rate_of_spread_c6(np.array([isi]))[0]
    expected = cffdrs.c6_calc.intermediate_surface_rate_of_spread_c6(isi)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)


@given(fuel_type=fuel_type, ros=ros, hr=hr, cfb=cfb)
@settings(deadline=None, max_examples=200)
def test_vectorized_distance_at_time_matches_reference(fuel_type, ros, hr, cfb):
    name, code = fuel_type
    actual = fbp.vectorized_distance_at_time(
        np.array([code]), np.array([ros]), np.array([hr]), np.array([cfb])
    )[0]
    expected = cffdrs.distance_at_time.distance_at_time(name, ros, hr, cfb)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)


@given(fc=fc, ros=ros)
@settings(deadline=None, max_examples=200)
def test_vectorized_fire_intensity_matches_reference(fc, ros):
    actual = fbp.vectorized_fire_intensity(np.array([fc]), np.array([ros]))[0]
    expected = cffdrs.fire_intensity.fire_intensity(fc, ros)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)


@given(lat=lat, lon=lon, elv=elv, day_of_year=day_of_year, d0=d0)
@settings(deadline=None, max_examples=200)
def test_vectorized_foliar_moisture_content_matches_reference(lat, lon, elv, day_of_year, d0):
    actual = fbp.vectorized_foliar_moisture_content(
        np.array([lat]), np.array([lon]), np.array([elv]), np.array([day_of_year]), np.array([d0])
    )[0]
    expected = cffdrs.foliar_moisture_content.foliar_moisture_content(lat, lon, elv, day_of_year, d0)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)


@given(fuel_type=fuel_type, wind_speed=wind_speed)
@settings(deadline=None, max_examples=200)
def test_vectorized_length_to_breadth_matches_reference(fuel_type, wind_speed):
    name, code = fuel_type
    actual = fbp.vectorized_length_to_breadth(np.array([code]), np.array([wind_speed]))[0]
    expected = cffdrs.length_to_breadth.length_to_breadth(name, wind_speed)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)


@given(fuel_type=fuel_type, lb=lb, hr=hr, cfb=cfb)
@settings(deadline=None, max_examples=200)
def test_vectorized_length_to_breadth_at_time_matches_reference(fuel_type, lb, hr, cfb):
    name, code = fuel_type
    actual = fbp.vectorized_length_to_breadth_at_time(
        np.array([code]), np.array([lb]), np.array([hr]), np.array([cfb])
    )[0]
    expected = cffdrs.length_to_breadth_at_time.length_to_breadth_at_time(name, lb, hr, cfb)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)


@given(fuel_type=fuel_type, ros=ros, hr=hr, cfb=cfb)
@settings(deadline=None, max_examples=200)
def test_vectorized_rate_of_spread_at_time_matches_reference(fuel_type, ros, hr, cfb):
    name, code = fuel_type
    actual = fbp.vectorized_rate_of_spread_at_time(
        np.array([code]), np.array([ros]), np.array([hr]), np.array([cfb])
    )[0]
    expected = cffdrs.rate_of_spread_at_time.rate_of_spread_at_time(name, ros, hr, cfb)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)


@given(fuel_type=fuel_type, ffmc=ffmc, bui=bui, pc=pc, gfl=gfl)
@settings(deadline=None, max_examples=200)
def test_vectorized_surface_fuel_consumption_matches_reference(fuel_type, ffmc, bui, pc, gfl):
    name, code = fuel_type
    actual = fbp.vectorized_surface_fuel_consumption(
        np.array([code]), np.array([ffmc]), np.array([bui]), np.array([pc]), np.array([gfl])
    )[0]
    expected = cffdrs.surface_fuel_consumption.surface_fuel_consumption(name, ffmc, bui, pc, gfl)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)


@given(csi=csi, sfc=sfc)
@settings(deadline=None, max_examples=200)
def test_vectorized_surface_fire_rate_of_spread_matches_reference(csi, sfc):
    actual = fbp.vectorized_surface_fire_rate_of_spread(np.array([csi]), np.array([sfc]))[0]
    expected = cffdrs.cfb_calc.surface_fire_rate_of_spread(csi, sfc)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)


@given(rsi=rsi, bui=bui)
@settings(deadline=None, max_examples=200)
def test_vectorized_surface_rate_of_spread_c6_matches_reference(rsi, bui):
    actual = fbp.vectorized_surface_rate_of_spread_c6(np.array([rsi]), np.array([bui]))[0]
    expected = cffdrs.c6_calc.surface_rate_of_spread_c6(rsi, bui)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)


@given(rsc=rsc, rss=rss, rso=rso)
@settings(deadline=None, max_examples=200)
def test_vectorized_crown_fraction_burned_c6_matches_reference(rsc, rss, rso):
    actual = fbp.vectorized_crown_fraction_burned_c6(np.array([rsc]), np.array([rss]), np.array([rso]))[0]
    expected = cffdrs.c6_calc.crown_fraction_burned_c6(rsc, rss, rso)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)


@given(fuel_type=fuel_type, cfl=cfl, cfb=cfb, sfc=sfc, pc=pc, pdf=pdf)
@settings(deadline=None, max_examples=200)
def test_vectorized_total_fuel_consumption_matches_reference(fuel_type, cfl, cfb, sfc, pc, pdf):
    name, code = fuel_type
    actual = fbp.vectorized_total_fuel_consumption(
        np.array([code]), np.array([cfl]), np.array([cfb]), np.array([sfc]), np.array([pc]), np.array([pdf])
    )[0]
    expected = cffdrs.total_fuel_consumption.total_fuel_consumption(name, cfl, cfb, sfc, pc, pdf)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)


@given(fuel_type=fuel_type, isi=isi, bui=bui, fmc=fmc, sfc=sfc, pc=pc, pdf=pdf, cc=cc, cbh=cbh)
@settings(deadline=None, max_examples=200)
def test_vectorized_rate_of_spread_matches_reference(fuel_type, isi, bui, fmc, sfc, pc, pdf, cc, cbh):
    name, code = fuel_type
    actual = fbp.vectorized_rate_of_spread(
        np.array([code]),
        np.array([isi]),
        np.array([bui]),
        np.array([fmc]),
        np.array([sfc]),
        np.array([pc]),
        np.array([pdf]),
        np.array([cc]),
        np.array([cbh]),
    )[0]
    expected = cffdrs.rate_of_spread.rate_of_spread(name, isi, bui, fmc, sfc, pc, pdf, cc, cbh)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)


@given(
    fuel_type=fuel_type,
    ffmc=ffmc,
    bui=bui,
    wind_speed=wind_speed,
    fmc=fmc,
    sfc=sfc,
    pc=pc,
    pdf=pdf,
    cc=cc,
    cbh=cbh,
)
@settings(deadline=None, max_examples=200)
def test_vectorized_back_rate_of_spread_matches_reference(
    fuel_type, ffmc, bui, wind_speed, fmc, sfc, pc, pdf, cc, cbh
):
    name, code = fuel_type
    actual = fbp.vectorized_back_rate_of_spread(
        np.array([code]),
        np.array([ffmc]),
        np.array([bui]),
        np.array([wind_speed]),
        np.array([fmc]),
        np.array([sfc]),
        np.array([pc]),
        np.array([pdf]),
        np.array([cc]),
        np.array([cbh]),
    )[0]
    expected = cffdrs.back_rate_of_spread.back_rate_of_spread(
        name, ffmc, bui, wind_speed, fmc, sfc, pc, pdf, cc, cbh
    )
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-9)


@given(
    fuel_type=fuel_type,
    ffmc=ffmc,
    bui=bui,
    wind_speed=wind_speed,
    waz=angle_rad,
    gs=gs,
    saz=angle_rad,
    fmc=fmc,
    sfc=sfc,
    pc=pc,
    pdf=pdf,
    cc=cc,
    cbh=cbh,
    isi=isi,
)
@settings(deadline=None, max_examples=200)
def test_vectorized_slope_adjustment_matches_reference(
    fuel_type, ffmc, bui, wind_speed, waz, gs, saz, fmc, sfc, pc, pdf, cc, cbh, isi
):
    name, code = fuel_type
    wsv_arr, raz_arr = fbp.vectorized_slope_adjustment(
        np.array([code]),
        np.array([ffmc]),
        np.array([bui]),
        np.array([wind_speed]),
        np.array([waz]),
        np.array([gs]),
        np.array([saz]),
        np.array([fmc]),
        np.array([sfc]),
        np.array([pc]),
        np.array([pdf]),
        np.array([cc]),
        np.array([cbh]),
        np.array([isi]),
    )
    expected = cffdrs.slope_calc.slope_adjustment(
        name, ffmc, bui, wind_speed, waz, gs, saz, fmc, sfc, pc, pdf, cc, cbh, isi
    )
    np.testing.assert_allclose(wsv_arr[0], expected.wsv, rtol=1e-6, atol=1e-9)
    np.testing.assert_allclose(raz_arr[0], expected.raz, rtol=1e-6, atol=1e-9)


@given(fuel_type=fuel_type, isi=isi, bui=bui, fmc=fmc, sfc=sfc, pc=pc, pdf=pdf, cc=cc, cbh=cbh)
@settings(deadline=None, max_examples=200)
def test_vectorized_rate_of_spread_extended_matches_reference(
    fuel_type, isi, bui, fmc, sfc, pc, pdf, cc, cbh
):
    name, code = fuel_type
    ros_arr, cfb_arr, csi_arr, rso_arr = fbp.vectorized_rate_of_spread_extended(
        np.array([code]),
        np.array([isi]),
        np.array([bui]),
        np.array([fmc]),
        np.array([sfc]),
        np.array([pc]),
        np.array([pdf]),
        np.array([cc]),
        np.array([cbh]),
    )
    expected = cffdrs.rate_of_spread.rate_of_spread_extended(name, isi, bui, fmc, sfc, pc, pdf, cc, cbh)
    np.testing.assert_allclose(ros_arr[0], expected.ros, rtol=1e-6, atol=1e-9)
    np.testing.assert_allclose(cfb_arr[0], expected.cfb, rtol=1e-6, atol=1e-9)
    np.testing.assert_allclose(csi_arr[0], expected.csi, rtol=1e-6, atol=1e-9)
    np.testing.assert_allclose(rso_arr[0], expected.rso, rtol=1e-6, atol=1e-9)
