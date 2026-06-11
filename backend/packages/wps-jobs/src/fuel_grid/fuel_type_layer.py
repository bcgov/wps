"""Functions for polygonizing the BC fuel type layer."""

import logging
from typing import Generator, Tuple

from osgeo import ogr, osr
from shapely import wkb, wkt

from wps_shared.geospatial.geospatial import NAD83_BC_ALBERS
from wps_shared.utils.polygonize import polygonize_in_memory
from wps_shared.utils.s3 import set_s3_gdal_config

logger = logging.getLogger(__name__)


def fuel_type_iterator_by_key(fuel_type_raster_key: str) -> Generator[Tuple[int, str], None, None]:
    """
    Yields fuel type id and geom by polygonizing fuel type layer raster stored in S3, and then
    iterating over feature from the resultant layer.

    NOTE: This works fine with a small FTL file, such as the SFMS one, but the high resolution
    FTL file uses a large amount of memory when polygonizing.
    """
    set_s3_gdal_config()
    logger.info("Polygonizing %s...", fuel_type_raster_key)
    with polygonize_in_memory(fuel_type_raster_key, "fuel", "fuel") as layer:
        spatial_reference: osr.SpatialReference = layer.GetSpatialRef()
        target_srs = osr.SpatialReference()
        target_srs.ImportFromEPSG(NAD83_BC_ALBERS)
        coordinate_transform = osr.CoordinateTransformation(spatial_reference, target_srs)

        logger.info("Iterating over features and inserting into database...")
        for i in range(layer.GetFeatureCount()):
            feature: ogr.Feature = layer.GetFeature(i)
            fuel_type_id = feature.GetField(0)
            geometry: ogr.Geometry = feature.GetGeometryRef()
            # keep derived geometries in the advisory shape projection.
            geometry.Transform(coordinate_transform)
            polygon = wkt.loads(geometry.ExportToIsoWkt())
            geom = wkb.dumps(polygon, hex=True, srid=NAD83_BC_ALBERS)
            yield (fuel_type_id, geom)
