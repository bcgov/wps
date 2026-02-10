"""
Unit tests for StationDewPointSource.
"""

from numpy.testing import assert_allclose

from wps_shared.schemas.sfms import SFMSDailyActual
from wps_sfms.interpolation.source import LAPSE_RATE, LapseRateAdjustedSource, StationDewPointSource


def _make_actual(code, lat, lon, elevation, temperature, relative_humidity):
    return SFMSDailyActual(
        code=code,
        lat=lat,
        lon=lon,
        elevation=elevation,
        temperature=temperature,
        relative_humidity=relative_humidity,
        precipitation=None,
        wind_speed=None,
    )


def test_dewpoint_computed_from_temp_and_rh():
    """Dew point values should match the simple approximation: Td = T - (100 - RH) / 5."""
    actuals = [
        _make_actual(1, 49.0, -123.0, 100.0, 20.0, 60.0),
        _make_actual(2, 49.1, -123.1, 200.0, 15.0, 80.0),
    ]
    source = StationDewPointSource(actuals)
    _, _, _, dewpoints = source.get_station_arrays(only_valid=True)

    expected_td_0 = 20.0 - (100.0 - 60.0) / 5.0  # = 12.0
    expected_td_1 = 15.0 - (100.0 - 80.0) / 5.0  # = 11.0
    assert_allclose(dewpoints[0], expected_td_0, atol=1e-4)
    assert_allclose(dewpoints[1], expected_td_1, atol=1e-4)


def test_missing_rh_excluded():
    """Stations with missing RH should be filtered out."""
    actuals = [
        _make_actual(1, 49.0, -123.0, 100.0, 20.0, 60.0),
        _make_actual(2, 49.1, -123.1, 200.0, 15.0, None),  # Missing RH
    ]
    source = StationDewPointSource(actuals)
    lats, _, _, dewpoints = source.get_station_arrays(only_valid=True)
    assert len(lats) == 1
    assert len(dewpoints) == 1


def test_missing_temp_excluded():
    """Stations with missing temperature should be filtered out (dewpoint can't be computed)."""
    actuals = [
        _make_actual(1, 49.0, -123.0, 100.0, None, 60.0),  # Missing temp
        _make_actual(2, 49.1, -123.1, 200.0, 15.0, 80.0),
    ]
    source = StationDewPointSource(actuals)
    lats, _, _, _ = source.get_station_arrays(only_valid=True)
    assert len(lats) == 1


def test_missing_elevation_excluded():
    """Stations with missing elevation should be filtered out."""
    actuals = [
        _make_actual(1, 49.0, -123.0, None, 20.0, 60.0),  # Missing elevation
        _make_actual(2, 49.1, -123.1, 200.0, 15.0, 80.0),
    ]
    source = StationDewPointSource(actuals)
    lats, _, _, _ = source.get_station_arrays(only_valid=True)
    assert len(lats) == 1


def test_get_interpolation_data_returns_sea_level_dewpoints():
    """get_interpolation_data should return sea-level adjusted dew points."""
    actuals = [
        _make_actual(1, 49.0, -123.0, 500.0, 20.0, 60.0),
    ]
    source = StationDewPointSource(actuals)
    _, _, sea_level_td = source.get_interpolation_data()

    _, _, _, raw_dewpoints = source.get_station_arrays(only_valid=True)
    _, _, elevs, _ = source.get_station_arrays(only_valid=True)

    # Sea level dew point should be warmer than actual (positive elevation)
    expected_sea = LapseRateAdjustedSource.compute_sea_level_values(
        raw_dewpoints, elevs, LAPSE_RATE
    )
    assert_allclose(sea_level_td, expected_sea, atol=1e-5)
    assert sea_level_td[0] > raw_dewpoints[0]


def test_empty_actuals():
    """Empty actuals should return empty arrays."""
    source = StationDewPointSource([])
    lats, lons, sea_td = source.get_interpolation_data()
    assert len(lats) == 0
    assert len(lons) == 0
    assert len(sea_td) == 0


def test_all_invalid_returns_empty():
    """If all stations have missing data, should return empty arrays."""
    actuals = [
        _make_actual(1, 49.0, -123.0, None, None, None),
        _make_actual(2, 49.1, -123.1, None, 15.0, None),
    ]
    source = StationDewPointSource(actuals)
    lats, _, _ = source.get_interpolation_data()
    assert len(lats) == 0


def test_station_count():
    """get_station_count should return total stations, not just valid ones."""
    actuals = [
        _make_actual(1, 49.0, -123.0, 100.0, 20.0, 60.0),
        _make_actual(2, 49.1, -123.1, None, 15.0, None),  # Invalid
    ]
    source = StationDewPointSource(actuals)
    assert source.get_station_count() == 2


def test_round_trip_lapse_rate():
    """Sea-level adjusted dew point adjusted back to station elevation should match original."""
    actuals = [
        _make_actual(1, 49.0, -123.0, 500.0, 25.0, 70.0),
        _make_actual(2, 49.1, -123.1, 1000.0, 10.0, 50.0),
    ]
    source = StationDewPointSource(actuals)
    _, _, elevs, original_td = source.get_station_arrays(only_valid=True)
    _, _, sea_td = source.get_interpolation_data()

    back = LapseRateAdjustedSource.compute_adjusted_values(sea_td, elevs, LAPSE_RATE)
    assert_allclose(back, original_td, atol=1e-4)
