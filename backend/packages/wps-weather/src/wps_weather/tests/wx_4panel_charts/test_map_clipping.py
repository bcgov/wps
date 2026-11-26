import cartopy.crs as ccrs
import matplotlib
import numpy as np
import pytest
import xarray as xr
from wps_weather.wx_4panel_charts.map_clipping import (
    ClipBounds,
    clip_to_bounds,
    visible_map_bounds,
)

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# Projection and extents used by the GDPS and RDPS plotter configs
CENTRAL_LONGITUDE = -130.0
CENTRAL_LATITUDE = 50.0
GDPS_EXTENT = [-170.0, -100.0, 30.0, 75.0]
RDPS_EXTENT = [-160.0, -100.0, 30.0, 70.0]

PANEL_GRID_POINTS = 300


def _visible_area_from_real_panel(extent):
    """
    Set up a map panel the same way the plotters do and return the lon/lat range
    it shows. visible_map_bounds does this without creating a panel; the test
    checks the two agree.
    """
    projection = ccrs.LambertConformal(
        central_longitude=CENTRAL_LONGITUDE, central_latitude=CENTRAL_LATITUDE
    )
    fig, ax = plt.subplots(subplot_kw={"projection": projection})
    try:
        ax.set_extent(extent, crs=ccrs.PlateCarree())
        x0, x1, y0, y1 = ax.get_extent()
    finally:
        plt.close(fig)

    # Sample the whole panel on a grid (a different method from the border walk in
    # visible_map_bounds) and convert to lon/lat.
    xs, ys = np.meshgrid(
        np.linspace(x0, x1, PANEL_GRID_POINTS), np.linspace(y0, y1, PANEL_GRID_POINTS)
    )
    points = ccrs.PlateCarree().transform_points(projection, xs.ravel(), ys.ravel())
    lons, lats = points[:, 0] % 360.0, points[:, 1]
    return lons.min(), lons.max(), lats.min(), lats.max()


@pytest.mark.parametrize("extent", [GDPS_EXTENT, RDPS_EXTENT], ids=["gdps", "rdps"])
def test_bounds_cover_the_whole_panel_plus_buffer(extent):
    buffer_deg = 2.0
    lon_min, lon_max, lat_min, lat_max = _visible_area_from_real_panel(extent)

    bounds = visible_map_bounds(extent, CENTRAL_LONGITUDE, CENTRAL_LATITUDE, buffer_deg)

    # Nothing visible on the panel, or within the buffer of its edge, is cut off.
    assert bounds.lon_min <= lon_min - buffer_deg
    assert bounds.lon_max >= lon_max + buffer_deg
    assert bounds.lat_min <= lat_min - buffer_deg
    assert bounds.lat_max >= lat_max + buffer_deg

    # Not much more than that either: rounding to whole degrees adds less than 1.
    assert bounds.lon_min > lon_min - buffer_deg - 1
    assert bounds.lon_max < lon_max + buffer_deg + 1
    assert bounds.lat_min > lat_min - buffer_deg - 1
    assert bounds.lat_max < lat_max + buffer_deg + 1


def test_gdps_style_grid_keeps_only_lats_and_lons_inside_bounds():
    lons = np.arange(0.0, 360.0, 10.0)  # 1-D, 0..350 like GDPS
    lats = np.arange(-90.0, 91.0, 10.0)
    ds = xr.Dataset(
        {"gh": (("latitude", "longitude"), np.zeros((len(lats), len(lons))))},
        coords={"latitude": lats, "longitude": lons},
    )

    clipped = clip_to_bounds(ds, ClipBounds(lon_min=150, lon_max=300, lat_min=20, lat_max=80))

    np.testing.assert_array_equal(clipped.longitude, np.arange(150.0, 301.0, 10.0))
    np.testing.assert_array_equal(clipped.latitude, np.arange(20.0, 81.0, 10.0))


def test_rdps_style_grid_keeps_smallest_row_col_block_containing_bounds():
    # 2-D lat/lon on y/x, longitudes in -180..180 like RDPS. Only two points are inside
    # the bounds: (row 1, col 0) at lon -170 (= 190) and (row 2, col 1) at lon -150 (= 210).
    lats = np.array(
        [
            [10.0, 10.0, 10.0, 10.0],
            [30.0, 30.0, 30.0, 30.0],
            [50.0, 50.0, 50.0, 50.0],
            [70.0, 70.0, 70.0, 70.0],
        ]
    )
    lons = np.array(
        [
            [100.0, 100.0, 100.0, 100.0],
            [-170.0, 100.0, 100.0, 100.0],
            [100.0, -150.0, 100.0, 100.0],
            [100.0, 100.0, 100.0, 100.0],
        ]
    )
    ds = xr.Dataset(
        {"gh": (("y", "x"), np.arange(16.0).reshape(4, 4))},
        coords={"latitude": (("y", "x"), lats), "longitude": (("y", "x"), lons)},
    )

    clipped = clip_to_bounds(ds, ClipBounds(lon_min=180, lon_max=220, lat_min=20, lat_max=60))

    # Rows 1-2 and columns 0-1: the block covering both points (it also includes two
    # points outside the bounds, since a block can't follow the grid's rotation).
    np.testing.assert_array_equal(clipped.gh, [[4.0, 5.0], [8.0, 9.0]])


def test_raises_when_no_grid_points_inside_bounds():
    lons = np.arange(150.0, 200.0, 10.0)
    lats = np.arange(30.0, 60.0, 10.0)
    ds = xr.Dataset(
        {"gh": (("latitude", "longitude"), np.zeros((len(lats), len(lons))))},
        coords={"latitude": lats, "longitude": lons},
    )

    with pytest.raises(ValueError):
        clip_to_bounds(ds, ClipBounds(lon_min=10, lon_max=20, lat_min=30, lat_max=50))
