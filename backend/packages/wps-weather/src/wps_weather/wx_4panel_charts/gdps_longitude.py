"""Longitude handling for the GDPS 4-panel chart plotters.

GDPS GRIB files store longitude as 0..360. The plotters, and the chart extents in
their configs, work in degrees west as negative numbers (e.g. -170..-100). How to
convert depends on whether the plotter received the full global grid or a grid
already clipped to the chart area.

GDPS only: RDPS uses 2-D lat/lon on a rotated grid, and even a clipped RDPS grid
contains near-pole points at every longitude, which would fool the global check.
"""

import numpy as np
from cartopy.util import add_cyclic_point


def _is_global(lons: np.ndarray) -> bool:
    """
    True if the grid wraps the whole globe, i.e. its span plus one grid step covers
    360 degrees. A full GDPS grid is 0..359.85 at 0.15 spacing (359.85 + 0.15 = 360);
    a grid clipped to the chart area spans ~150 degrees.
    """
    if len(lons) < 2:
        return False
    spacing = abs(float(lons[1] - lons[0]))
    span = float(lons.max() - lons.min())
    return bool(np.isclose(span + spacing, 360.0))


def prepare_gdps_lon_axis(
    lons: np.ndarray, *fields: np.ndarray
) -> tuple[np.ndarray, list[np.ndarray]]:
    """
    Turn a GDPS 0..360 longitude axis, and the fields on it, into a form ready to plot.

    - Global grid: wrap longitudes to -180..180, re-sort the columns into that order,
      and add a cyclic column so there is no seam at the dateline.
    - Clipped grid (e.g. 148..299): subtract 360 from every longitude (-212..-61).
      The columns keep their order, so the axis stays increasing across the dateline
      and lines up with the extents in the plotter configs. No re-sort and no cyclic
      column: the clipped region doesn't wrap around the globe.

    :param lons: 1-D longitudes in 0..360, one per column of each field.
    :param fields: 2-D (lat, lon) arrays to transform the same way as the longitudes.
    :return: (lon_plot, [field, ...]) with the fields in the order they were passed.
    """
    if _is_global(lons):
        # Global branch preserves the original behaviour, which loads full GDPS GRIB files.
        # If there is no use case for full GDPS GRIB files, this branch could be removed.
        lon_wrapped = ((lons + 180.0) % 360.0) - 180.0
        order = np.argsort(lon_wrapped)
        lon_sorted = lon_wrapped[order]

        lon_plot = lon_sorted
        prepared = []
        for field in fields:
            field_cyclic, lon_plot = add_cyclic_point(field[:, order], coord=lon_sorted)
            prepared.append(field_cyclic)
        return lon_plot, prepared

    lon_plot = lons - 360.0 if lons.max() > 180.0 else lons.copy()
    return lon_plot, list(fields)
