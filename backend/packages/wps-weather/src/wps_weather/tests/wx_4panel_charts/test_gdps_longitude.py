import numpy as np
from cartopy.util import add_cyclic_point
from wps_weather.wx_4panel_charts.gdps_longitude import prepare_gdps_lon_axis


def _old_plotter_lon_handling(lons, field):
    """The longitude code the GDPS plotters used before clipping was added."""
    lon_wrapped = ((lons + 180.0) % 360.0) - 180.0
    order = np.argsort(lon_wrapped)
    lon_plot = lon_wrapped[order]
    field_cyclic, lon_plot_cyclic = add_cyclic_point(field[:, order], coord=lon_plot)
    return lon_plot_cyclic, field_cyclic


def _make_field(n_lons, n_lats=3):
    """Return a small (lat, lon) array of seeded random values standing in for a weather field."""
    return np.random.default_rng(0).random((n_lats, n_lons))


def test_global_grid_matches_old_plotter_behaviour():
    lons = np.arange(0.0, 360.0, 30.0)  # 0..330, global
    field = _make_field(len(lons))

    expected_lon, expected_field = _old_plotter_lon_handling(lons, field)
    lon_plot, (prepared,) = prepare_gdps_lon_axis(lons, field)

    np.testing.assert_array_equal(lon_plot, expected_lon)
    np.testing.assert_array_equal(prepared, expected_field)
    assert len(lon_plot) == len(lons) + 1  # cyclic column added


def test_clipped_grid_across_dateline_is_shifted_not_split():
    lons = np.arange(150.0, 300.0, 10.0)  # 150..290, crosses 180
    field = _make_field(len(lons))

    lon_plot, (prepared,) = prepare_gdps_lon_axis(lons, field)

    np.testing.assert_array_equal(lon_plot, lons - 360.0)  # -210..-70
    assert np.all(np.diff(lon_plot) > 0)  # strictly increasing, no jump at the dateline
    np.testing.assert_array_equal(prepared, field)  # no re-sort, no cyclic column


def test_clipped_grid_west_of_dateline_is_unchanged():
    lons = np.arange(100.0, 180.0, 10.0)  # never over 180, nothing to shift

    lon_plot, _ = prepare_gdps_lon_axis(lons, _make_field(len(lons)))

    np.testing.assert_array_equal(lon_plot, lons)
