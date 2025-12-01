import numpy as np
from geoalchemy2.shape import to_shape
from osgeo import gdal, osr

from wps_shared.geospatial.geospatial import prepare_wkt_geom_for_gdal
from wps_shared.utils.s3 import set_s3_gdal_config


def calculate_fuel_type_area_for_zone(advisory_shape_id: int, data: np.ndarray, pixel_size: int):
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


def calculate_fuel_type_areas_per_zone(fuel_raster_key: str, zones):
    set_s3_gdal_config()
    fuel_raster_ds: gdal.Dataset = gdal.Open(fuel_raster_key, gdal.GA_ReadOnly)
    pixel_size = fuel_raster_ds.GetGeoTransform()[1]
    # We're using fire zone units from the advisory_shapes table to clip out shapes from the fuel raster.
    # We need to manually specify the spatial reference of the advisory_shapes table in the gdal.WarpOptions below.
    source_srs = osr.SpatialReference()
    source_srs.ImportFromEPSG(3005)
    for zone in zones:
        zone_wkb = zone.geom
        shapely_zone_geom = to_shape(zone_wkb)
        zone_wkt = shapely_zone_geom.wkt
        zone_geom = prepare_wkt_geom_for_gdal(zone_wkt, source_srs)

        # Use gdal.Warp to clip out our fire zone unit from the masked tpi raster
        warp_options = gdal.WarpOptions(
            cutlineWKT=zone_geom,
            cutlineSRS=zone_geom.GetSpatialReference(),
            cropToCutline=True,
        )
        intersected_path = "/vsimem/intersected.tif"
        intersected_ds: gdal.Dataset = gdal.Warp(
            intersected_path, fuel_raster_ds, options=warp_options
        )
        intersected_band: gdal.Band = intersected_ds.GetRasterBand(1)
        intersected_data: np.ndarray = intersected_band.ReadAsArray()
        intersected_ds = None
        fuel_type_area_data = calculate_fuel_type_area_for_zone(
            zone.id, intersected_data, pixel_size
        )
        yield fuel_type_area_data
