import numpy as np
from numpy.testing import assert_allclose

from app.sfms.interpolation_source import LAPSE_RATE, StationTemperatureSource


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
