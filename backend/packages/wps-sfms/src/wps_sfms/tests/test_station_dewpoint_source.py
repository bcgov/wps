"""
Unit tests for StationDewPointSource.
"""

from numpy.testing import assert_allclose

from wps_shared.schemas.sfms import SFMSDailyActual
from wps_sfms.interpolation.source import (
    DEW_POINT_LAPSE_RATE,
    LapseRateAdjustedSource,
    StationDewPointSource,
)


def _make_actual(code, lat, lon, elevation, dewpoint):
    return SFMSDailyActual(
        code=code,
        lat=lat,
        lon=lon,
        elevation=elevation,
        dewpoint=dewpoint,
    )


def test_dewpoint_values_read_directly():
    """Dew point values should be read directly from actuals."""
    actuals = [
        _make_actual(1, 49.0, -123.0, 100.0, 12.0),
        _make_actual(2, 49.1, -123.1, 200.0, 11.0),
    ]
    source = StationDewPointSource(actuals)
    _, _, _, dewpoints = source.get_station_arrays(only_valid=True)

    assert_allclose(dewpoints[0], 12.0, atol=1e-4)
    assert_allclose(dewpoints[1], 11.0, atol=1e-4)


def test_missing_dewpoint_excluded():
    """Stations with missing dewpoint should be filtered out."""
    actuals = [
        _make_actual(1, 49.0, -123.0, 100.0, 12.0),
        _make_actual(2, 49.1, -123.1, 200.0, None),  # Missing dewpoint
    ]
    source = StationDewPointSource(actuals)
    lats, _, _, dewpoints = source.get_station_arrays(only_valid=True)
    assert len(lats) == 1
    assert len(dewpoints) == 1


def test_missing_elevation_excluded():
    """Stations with missing elevation should be filtered out."""
    actuals = [
        _make_actual(1, 49.0, -123.0, None, 12.0),  # Missing elevation
        _make_actual(2, 49.1, -123.1, 200.0, 11.0),
    ]
    source = StationDewPointSource(actuals)
    lats, _, _, _ = source.get_station_arrays(only_valid=True)
    assert len(lats) == 1


def test_get_interpolation_data_returns_sea_level_dewpoints():
    """get_interpolation_data should return sea-level adjusted dew points."""
    actuals = [
        _make_actual(1, 49.0, -123.0, 500.0, 12.0),
    ]
    source = StationDewPointSource(actuals)
    _, _, sea_level_td = source.get_interpolation_data(lapse_rate=DEW_POINT_LAPSE_RATE)

    _, _, _, raw_dewpoints = source.get_station_arrays(only_valid=True)
    _, _, elevs, _ = source.get_station_arrays(only_valid=True)

    # Sea level dew point should be warmer than actual (positive elevation)
    expected_sea = LapseRateAdjustedSource.compute_sea_level_values(
        raw_dewpoints, elevs, DEW_POINT_LAPSE_RATE
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
        _make_actual(1, 49.0, -123.0, None, None),
        _make_actual(2, 49.1, -123.1, None, None),
    ]
    source = StationDewPointSource(actuals)
    lats, _, _ = source.get_interpolation_data()
    assert len(lats) == 0


def test_station_count():
    """get_station_count should return total stations, not just valid ones."""
    actuals = [
        _make_actual(1, 49.0, -123.0, 100.0, 12.0),
        _make_actual(2, 49.1, -123.1, None, None),  # Invalid
    ]
    source = StationDewPointSource(actuals)
    assert source.get_station_count() == 2


def test_round_trip_lapse_rate():
    """Sea-level adjusted dew point adjusted back to station elevation should match original."""
    actuals = [
        _make_actual(1, 49.0, -123.0, 500.0, 19.0),
        _make_actual(2, 49.1, -123.1, 1000.0, 0.0),
    ]
    source = StationDewPointSource(actuals)
    _, _, elevs, original_td = source.get_station_arrays(only_valid=True)
    _, _, sea_td = source.get_interpolation_data(lapse_rate=DEW_POINT_LAPSE_RATE)

    back = LapseRateAdjustedSource.compute_adjusted_values(sea_td, elevs, DEW_POINT_LAPSE_RATE)
    assert_allclose(back, original_td, atol=1e-4)
