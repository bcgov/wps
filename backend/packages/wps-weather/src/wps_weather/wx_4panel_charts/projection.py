"""Chart projection with empty-geometry support for Cartopy 0.25."""

from cartopy.crs import LambertConformal


class ChartLambertConformal(LambertConformal):
    def project_geometry(self, geometry, src_crs=None):
        # Cartopy drops zero-area contour polygons when converting paths to
        # geometry. If none remain, 0.25 tries to read x/y from an empty Point
        # and aborts the entire chart. Empty geometry has nothing to project.
        if geometry.is_empty:
            return geometry
        return super().project_geometry(geometry, src_crs)
