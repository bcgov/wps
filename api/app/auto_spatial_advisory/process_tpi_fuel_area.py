from typing import Optional

import numpy as np
from geoalchemy2.shape import to_shape
from osgeo import gdal, ogr, osr

from wps_shared import config
from wps_shared.db.models.auto_spatial_advisory import TPIClassEnum
from wps_shared.geospatial.geospatial import prepare_wkt_geom_for_gdal
from wps_shared.utils.s3 import set_s3_gdal_config


def calculate_tpi_area_data_for_zone(advisory_shape_id: int, data: np.ndarray, pixel_size: int):
    """
    Save TPIFuelArea records to the API database.

        :param advisory_shape_id: A fire zone id used as a foreign key to the advisory_shapes table.
        :param data: A numpy ndarray containing classified TPI values that have been masked by the fuel layer.
        :param pixel_size: The size of the cells in the TPI layer.
    """
    unique_values, counts = np.unique(data, return_counts=True)
    for value, count in zip(unique_values, counts):
        if value in TPIClassEnum:
            tpi_enum = TPIClassEnum(value)
            fuel_area = count * pixel_size * pixel_size
            yield (advisory_shape_id, tpi_enum, fuel_area)


def calculate_masked_tpi_areas(zones, key: Optional[str] = None):
    """
    Entry point for calculating the fuel layer masked area of each TPI class (valley bottom, mid slope and upper slope) per fire zone unit.
    """
    set_s3_gdal_config()
    bucket = config.get("OBJECT_STORE_BUCKET")
    filename = key if key is not None else config.get("CLASSIFIED_TPI_DEM_FUEL_MASKED_NAME")
    masked_tpi_key = f"/vsis3/{bucket}/dem/tpi/{filename}"
    masked_tpi_ds: gdal.Dataset = gdal.Open(masked_tpi_key, gdal.GA_ReadOnly)
    masked_tpi_pixel_size = masked_tpi_ds.GetGeoTransform()[1]
    masked_tpi_srs = masked_tpi_ds.GetSpatialRef()

    for zone in zones:
        zone_wkb = zone.geom
        shapely_zone_geom = to_shape(zone_wkb)
        zone_wkt = shapely_zone_geom.wkt
        zone_geom = prepare_wkt_geom_for_gdal(zone_wkt, masked_tpi_srs)

        # Use gdal.Warp to clip out our fire zone unit from the masked tpi raster
        warp_options = gdal.WarpOptions(
            cutlineWKT=zone_geom, cutlineSRS=zone_geom.GetSpatialReference(), cropToCutline=True
        )
        intersected_path = "/vsimem/intersected.tif"
        intersected_ds: gdal.Dataset = gdal.Warp(
            intersected_path, masked_tpi_ds, options=warp_options
        )
        intersected_band: gdal.Band = intersected_ds.GetRasterBand(1)
        intersected_data: np.ndarray = intersected_band.ReadAsArray()
        intersected_ds = None
        tpi_area_data = calculate_tpi_area_data_for_zone(
            advisory_shape_id=zone.id, data=intersected_data, pixel_size=masked_tpi_pixel_size
        )
        for tpi_area in tpi_area_data:
            yield tpi_area
    masked_tpi_ds = None
