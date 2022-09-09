import asyncio
import logging
from osgeo import ogr, osr
from shapely import wkt, wkb
from app.auto_spatial_advisory.polygonize import polygonize
from app.db.models.auto_spatial_advisory import FuelType
from app.db.database import get_async_write_session_scope
from app.db.crud.auto_spatial_advisory import save_fuel_type
from app.geospatial import NAD83_BC_ALBERS


logger = logging.getLogger(__name__)


async def main():
    """Main entry point for the script."""
    # key = f'/vsis3/{bucket}/sfms/uploads/{run_type.value}/{run_date.isoformat()}/hfi{for_date_string}.tif'
    # filename = '/home/sybrand/ftl/ftl_2018/ftl2018.bin'
    filename = '/home/sybrand/ftl/fbp2021.tif'
    logger.info('start polygonize')
    ds, layer = polygonize(filename)

    spatial_reference: osr.SpatialReference = layer.GetSpatialRef()
    target_srs = osr.SpatialReference()
    target_srs.ImportFromEPSG(NAD83_BC_ALBERS)
    coordinate_transform = osr.CoordinateTransformation(spatial_reference, target_srs)

    logger.info('save to database')
    async with get_async_write_session_scope() as session:
        for i in range(layer.GetFeatureCount()):
            feature: ogr.Feature = layer.GetFeature(i)
            fuel_type = feature.GetField(0)
            geometry: ogr.Geometry = feature.GetGeometryRef()
            # Make sure the geometry is in EPSG:3005!
            geometry.Transform(coordinate_transform)
            polygon = wkt.loads(geometry.ExportToIsoWkt())

            obj = FuelType(fuel_type_id=fuel_type, geom=wkb.dumps(polygon,
                                                                  hex=True,
                                                                  srid=NAD83_BC_ALBERS))

            await save_fuel_type(session, obj)

    del ds, layer


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
