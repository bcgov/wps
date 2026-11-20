"""Work out which part of a GRIB grid a 4-panel chart actually shows, so the rest can be
dropped before the data is loaded.

The charts use a Lambert Conformal projection, so the rectangular panel shows more than
the chart's extent: much more longitude (especially in the top corners) and a little more
latitude. The bounds are found by tracing the panel's border back to lon/lat, rather than
by adding a fixed margin to the extent, so they stay correct if the extent changes.
"""

import math
from typing import NamedTuple

import cartopy.crs as ccrs
import numpy as np
import xarray as xr
from shapely.geometry import LineString

# Extra margin on every edge, so contours and high/low detection have data just past
# the edge of the panel.
CLIP_BUFFER_DEG = 2.0

# Points sampled along each side of the panel border when tracing it back to lon/lat.
BORDER_POINTS_PER_SIDE = 200


class ClipBounds(NamedTuple):
    """Area to keep. Longitudes are 0..360 (the GRIB convention), latitudes -90..90."""

    lon_min: float
    lon_max: float
    lat_min: float
    lat_max: float


def visible_map_bounds(
    extent: list[float],
    central_longitude: float,
    central_latitude: float,
    buffer_deg: float = CLIP_BUFFER_DEG,
) -> ClipBounds:
    """
    Takes the extent as in the plotter configs (-180..180) and returns a lon/lat box
    covering everything visible in a chart panel, plus a buffer. Converts longitudes to
    0..360 to match the GRIB files.

    Example: the GDPS extent [-170, -100, 30, 75] shows roughly lon 150.6..297.0 and
    lat 23.9..77.2, so with the 2 degree buffer this returns (148, 300, 21, 80).
    """
    lon_min, lon_max, lat_min, lat_max = extent
    plate_carree = ccrs.PlateCarree()
    projection = ccrs.LambertConformal(
        central_longitude=central_longitude, central_latitude=central_latitude
    )

    # 1) The panel rectangle in map coordinates. This is how ax.set_extent works out
    #    the panel: project the extent box and take the smallest rectangle around it.
    extent_box = LineString(
        [
            (lon_min, lat_min),
            (lon_max, lat_min),
            (lon_max, lat_max),
            (lon_min, lat_max),
            (lon_min, lat_min),
        ]
    )
    x0, y0, x1, y1 = projection.project_geometry(extent_box, plate_carree).bounds

    # 2) Walk around the rectangle's border and convert each point back to lon/lat.
    n = BORDER_POINTS_PER_SIDE
    xs = np.concatenate(
        [np.linspace(x0, x1, n), np.full(n, x1), np.linspace(x1, x0, n), np.full(n, x0)]
    )
    ys = np.concatenate(
        [np.full(n, y0), np.linspace(y0, y1, n), np.full(n, y1), np.linspace(y1, y0, n)]
    )
    border = plate_carree.transform_points(projection, xs, ys)
    border_lons = border[:, 0] % 360.0
    border_lats = border[:, 1]

    # 3) Add the buffer and round outward, so the box never shrinks.
    return ClipBounds(
        lon_min=math.floor(border_lons.min() - buffer_deg),
        lon_max=math.ceil(border_lons.max() + buffer_deg),
        lat_min=math.floor(border_lats.min() - buffer_deg),
        lat_max=math.ceil(border_lats.max() + buffer_deg),
    )


def clip_to_bounds(ds: xr.Dataset, bounds: ClipBounds) -> xr.Dataset:
    """
    Cut a GRIB dataset down to the smallest block of the grid that covers the bounds.
    Call it before ds.load(), so only the kept block is read into memory.

    - GDPS (1-D latitude/longitude): keep the latitudes and longitudes inside the bounds.
    - RDPS (2-D latitude/longitude on a rotated y/x grid): mark the points inside the
      bounds, then keep the smallest block of rows and columns that contains all of them.
      Some points in that block fall outside the bounds; the grid's rows and columns
      don't line up with lat/lon lines.

    Raises ValueError if no grid points fall inside the bounds.
    """
    lons = ds["longitude"] % 360.0  # RDPS uses -180..180, GDPS already 0..360
    lats = ds["latitude"]
    in_lon = (lons >= bounds.lon_min) & (lons <= bounds.lon_max)
    in_lat = (lats >= bounds.lat_min) & (lats <= bounds.lat_max)

    if lons.ndim == 1:
        if not (in_lon.any() and in_lat.any()):
            raise ValueError(f"No grid points inside {bounds}")
        return ds.isel(longitude=in_lon.values, latitude=in_lat.values)

    inside = (in_lon & in_lat).values
    if not inside.any():
        raise ValueError(f"No grid points inside {bounds}")
    y_dim, x_dim = lons.dims
    rows = np.flatnonzero(inside.any(axis=1))  # rows with at least one inside point
    cols = np.flatnonzero(inside.any(axis=0))  # columns with at least one inside point

    # One continuous block from the first to the last of those rows/columns, so no
    # rows or columns are skipped in the middle of the grid.
    row_block = slice(rows[0], rows[-1] + 1)
    col_block = slice(cols[0], cols[-1] + 1)
    return ds.isel({y_dim: row_block, x_dim: col_block})
