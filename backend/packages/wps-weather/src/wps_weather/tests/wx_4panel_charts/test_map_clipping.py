import cartopy.crs as ccrs
import matplotlib
import numpy as np
import pytest
from wps_weather.wx_4panel_charts.map_clipping import visible_map_bounds

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
