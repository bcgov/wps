"""Exercise real Cartopy transforms and PNG rendering, without weather services."""

from io import BytesIO

import cartopy.crs as ccrs
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from cartopy.mpl.geoaxes import InterProjectionTransform
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from shapely.geometry import LineString, Point, Polygon
from wps_weather.wx_4panel_charts.projection import ChartLambertConformal


@pytest.mark.parametrize("geometry", [Point(), LineString(), Polygon()])
def test_empty_geometry_remains_empty(geometry):
    assert ChartLambertConformal().project_geometry(geometry, ccrs.PlateCarree()).is_empty


def test_zero_area_contour_does_not_abort_chart_rendering():
    # A closed contour with collinear vertices has zero area. Cartopy converts
    # it to an empty Point; 0.25's ordinary LambertConformal raises GEOSException.
    path = Path(
        [(-130, 50), (-129, 50), (-128, 50), (-127, 50), (-130, 50)],
        [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY],
    )
    projection = ChartLambertConformal(central_longitude=-130, central_latitude=50)
    transformed = InterProjectionTransform(
        ccrs.PlateCarree(), projection
    ).transform_path_non_affine(path)
    assert transformed.vertices.size == 0

    fig, ax = plt.subplots(subplot_kw={"projection": projection})
    try:
        ax.set_extent([-140, -110, 40, 65], crs=ccrs.PlateCarree())
        ax.add_patch(PathPatch(path, transform=ccrs.PlateCarree()))
        # Nonempty contours must still render alongside the degenerate one.
        ax.contourf(
            [-140, -125, -110],
            [40, 50, 65],
            [[0, 1, 0], [1, 2, 1], [0, 1, 0]],
            transform=ccrs.PlateCarree(),
        )
        output = BytesIO()
        fig.savefig(output, format="png")
        assert output.getvalue().startswith(b"\x89PNG\r\n\x1a\n")
    finally:
        plt.close(fig)


def test_nonempty_geometry_uses_the_original_projection():
    source = ccrs.PlateCarree()
    geometry = Polygon([(-135, 45), (-120, 45), (-120, 60), (-135, 45)])
    expected = ccrs.LambertConformal().project_geometry(geometry, source)
    actual = ChartLambertConformal().project_geometry(geometry, source)
    assert actual.equals_exact(expected, tolerance=1e-8)
    np.testing.assert_allclose(
        ChartLambertConformal().transform_points(source, np.array([-130.0]), np.array([50.0])),
        ccrs.LambertConformal().transform_points(source, np.array([-130.0]), np.array([50.0])),
    )
