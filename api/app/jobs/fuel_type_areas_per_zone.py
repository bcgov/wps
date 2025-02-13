import os
import sys
from osgeo import gdal, osr
from geoalchemy2.shape import to_shape
import asyncio
import logging
import numpy as np

from wps_shared.logging import configure_logging
from wps_shared.db.crud.auto_spatial_advisory import get_fire_zone_unit_shape_type_id, get_fire_zone_units
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.auto_spatial_advisory import AdvisoryShapeFuels
from wps_shared import config
from wps_shared.rocketchat_notifications import send_rocketchat_notification
from wps_shared.geospatial.geospatial import prepare_wkt_geom_for_gdal
from wps_shared.utils.s3 import set_s3_gdal_config


logger = logging.getLogger(__name__)


class FuelTypeAreasJob:
    def _save_fuel_type_area(self, session, advisory_shape_id, fuel_type_id, fuel_area):
        fuel_type_area = AdvisoryShapeFuels(advisory_shape_id=advisory_shape_id, fuel_type=fuel_type_id, fuel_area=fuel_area)
        session.add(fuel_type_area)

    def _calculate_fuel_type_area_for_zone(self, advisory_shape_id: int, data: np.ndarray, pixel_size: int):
        """
        Calculate the area of each fuel type in a fire zone unit.

        :param advisory_shape_id: The id of the fire zone unit.
        :param data: A numpy ndarray containing fuel type values.
        :param pixel_size: The size of the cells in the fuel layer.
        """
        unique_values, counts = np.unique(data, return_counts=True)
        for value, count in zip(unique_values, counts):
            if value > 0 and value < 99:
                fuel_area = count * pixel_size * pixel_size
                yield (advisory_shape_id, value, fuel_area)

    async def calculate_fuel_type_areas_per_zone(self):
        """
        Entry point for calculating the area of each fuel type in each fire zone unit.
        """

        set_s3_gdal_config()
        bucket = config.get("OBJECT_STORE_BUCKET")
        fuel_raster_name = config.get("FUEL_RASTER_NAME")
        fuel_raster_key = f"/vsis3/{bucket}/sfms/static/{fuel_raster_name}"
        fuel_raster_ds: gdal.Dataset = gdal.Open(fuel_raster_key, gdal.GA_ReadOnly)
        pixel_size = fuel_raster_ds.GetGeoTransform()[1]
        # We're using fire zone units from the advisory_shapes table to clip out shapes from the fuel raster.
        # We need to manually specify the spatial reference of the advisory_shapes table in the gdal.WarpOptions below.
        source_srs = osr.SpatialReference()
        source_srs.ImportFromEPSG(3005)

        async with get_async_write_session_scope() as session:
            shape_type_id = await get_fire_zone_unit_shape_type_id(session)
            zones = await get_fire_zone_units(session, shape_type_id)
            for zone in zones:
                zone_wkb = zone[0].geom
                shapely_zone_geom = to_shape(zone_wkb)
                zone_wkt = shapely_zone_geom.wkt
                zone_geom = prepare_wkt_geom_for_gdal(zone_wkt, source_srs)

                # Use gdal.Warp to clip out our fire zone unit from the masked tpi raster
                warp_options = gdal.WarpOptions(cutlineWKT=zone_geom, cutlineSRS=zone_geom.GetSpatialReference(), cropToCutline=True)
                intersected_path = "/vsimem/intersected.tif"
                intersected_ds: gdal.Dataset = gdal.Warp(intersected_path, fuel_raster_ds, options=warp_options)
                intersected_band: gdal.Band = intersected_ds.GetRasterBand(1)
                intersected_data: np.ndarray = intersected_band.ReadAsArray()
                intersected_ds = None
                fuel_type_area_data = self._calculate_fuel_type_area_for_zone(zone[0].id, intersected_data, pixel_size)
                for advisory_shape_id, fuel_type_id, fuel_area in fuel_type_area_data:
                    self._save_fuel_type_area(session, advisory_shape_id, fuel_type_id, fuel_area)
        fuel_raster_ds = None


def main():
    """Kicks off populating the advisory_shape_fuels table."""
    try:
        # We don't want gdal to silently swallow errors.
        gdal.UseExceptions()
        logger.debug("Begin processing fuel types area per zone.")

        job = FuelTypeAreasJob()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(job.calculate_fuel_type_areas_per_zone())

        # Exit with 0 - success.
        sys.exit(os.EX_OK)
    except Exception as exception:
        # Exit non 0 - failure.
        logger.error("An error occurred while processing fuel types area per zone.", exc_info=exception)
        rc_message = ":scream: Encountered an error while processing fuel types area per zone."
        send_rocketchat_notification(rc_message, exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()