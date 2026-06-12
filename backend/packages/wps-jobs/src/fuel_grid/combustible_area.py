"""
calculate_combustible_land_area.py iterates calculates the total land area covered by combustible
fuels in each fire zone.

The fuel types vector file is retrieved from our object store bucket, and the fire zones
(simplified polygons) are pulled from our database.
"""

from typing import Generator, Tuple

from geoalchemy2.shape import to_shape
from osgeo import ogr


def calculate_combustible_area_by_fire_zone(
    fuel_types_layer, zones
) -> Generator[Tuple[str, float, int], None, None]:
    """
    Given layer of combustible fuel types for BC and fire zone ID and geometry,
    calculates the intersection of zone geom and combustible fuels.
    Yields fire zone's combustible area in square metres.
    """
    for zone in zones:
        zone_wkb = zone.geom
        shapely_zone_geom = to_shape(zone_wkb)
        zone_wkt = shapely_zone_geom.wkt
        zone_geom = ogr.CreateGeometryFromWkt(zone_wkt)
        fuel_types_layer.SetSpatialFilter(zone_geom)
        # create GeometryCollection of all filtered fuel type polygons
        geom_collection = ogr.Geometry(ogr.wkbGeometryCollection)
        for fuel_type_geom in fuel_types_layer:
            geom_collection.AddGeometry(fuel_type_geom.geometry())
        # ensure the GeometryCollection is valid
        geom_collection_valid = geom_collection.MakeValid()
        # this line is necessary because otherwise Fraser Fire Zone can't undergo spatial
        # comparison for calculating Intersection. Likely due to the fuel types polygons
        # self-intersecting somewhere within the Fraser Fire Zone. Buffer(0) tries to
        # correct the self-intersection by "guessing", but it isn't always right.
        # https://gis.stackexchange.com/questions/311209/how-to-fix-invalid-polygon-with-self-intersection-python
        buffered_geom_collection = geom_collection_valid.Buffer(0)
        # get intersection
        intersection = buffered_geom_collection.Intersection(zone_geom)
        if intersection is not None and intersection.GetArea() > 0:
            yield (str(zone.source_identifier), intersection.GetArea(), zone.id)
        else:
            yield (None, None, None)
