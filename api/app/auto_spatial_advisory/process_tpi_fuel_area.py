import numpy as np
from osgeo import gdal, ogr, osr

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app import config
from app.db.database import get_write_session_scope
from app.db.models.auto_spatial_advisory import Shape, TPIClassEnum, TPIFuelArea
from app.utils.s3 import set_s3_gdal_config


def store_tpi_area_data(session: Session, advisory_shape_id: int, data: np.ndarray, pixel_size: int):
    """
    Save TPIFuelArea records to the API database.

        :param session: A synchronous sqlalchemy session object.
        :param advisory_shape_id: A fire zone id used as a foreign key to the advisory_shapes table.
        :param data: A numpy ndarray containing classified TPI values that have been masked by the fuel layer.
        :param pixel_size: The size of the cells in the TPI layer.
    """
    unique_values, counts = np.unique(data, return_counts=True)
    for value, count in zip(unique_values, counts):
        if value in TPIClassEnum:
            tpi_enum = TPIClassEnum(value)
            fuel_area = count * pixel_size * pixel_size
            tpi_fuel_area = TPIFuelArea(advisory_shape_id=advisory_shape_id, tpi_class=tpi_enum, fuel_area=fuel_area)
            session.add(tpi_fuel_area)


def prepare_wkt_geom_for_gdal(wkt_geom: str):
    """
    Given a wkt geometry as a string, convert it to an ogr.Geometry that can be used by gdal.

    :param wkt_geom: The wky geometry string.
    :return: An osr.Geometry.
    """
    geometry: ogr.Geometry = ogr.CreateGeometryFromWkt(wkt_geom)
    source_srs = osr.SpatialReference()
    source_srs.ImportFromEPSG(3005)
    geometry.AssignSpatialReference(source_srs)
    transform = osr.CoordinateTransformation(geometry.GetSpatialReference(), source_srs)
    geometry.Transform(transform)
    return geometry


def process_tpi_fuel_area():
    """
    Entry point for calculating the fuel layer masked area of each TPI class (valley bottom, mid slope and upper slope) per fire zone unit.
    """
    set_s3_gdal_config()
    bucket = config.get("OBJECT_STORE_BUCKET")
    masked_tpi_key = f"/vsis3/{bucket}/dem/tpi/{config.get("CLASSIFIED_TPI_DEM_FUEL_MASKED_NAME")}"
    masked_tpi_ds: gdal.Dataset = gdal.Open(masked_tpi_key, gdal.GA_ReadOnly)
    masked_tpi_pixel_size = masked_tpi_ds.GetGeoTransform()[1]

    with get_write_session_scope() as session:
        # Iterate through the fire zone units from the advisory_shapes table
        stmt = select(Shape.id, func.ST_AsText(Shape.geom))
        result = session.execute(stmt)
        for row in result:
            # Convert the WKT geometry of a fire zone unit into a form that can be used by gdal
            geometry = prepare_wkt_geom_for_gdal(row[1])

            # Us gdal.Warp to clip out our fire zone unit from the masked tpi raster and then store areas in the tpi_fuel_area table
            warp_options = gdal.WarpOptions(cutlineWKT=geometry, cutlineSRS=geometry.GetSpatialReference(), cropToCutline=True)
            intersected_path = "/vsimem/intersected.tif"
            intersected_ds: gdal.Dataset = gdal.Warp(intersected_path, masked_tpi_ds, options=warp_options)
            intersected_band: gdal.Band = intersected_ds.GetRasterBand(1)
            intersected_data: np.ndarray = intersected_band.ReadAsArray()
            store_tpi_area_data(session, advisory_shape_id=row[0], data=intersected_data, pixel_size=masked_tpi_pixel_size)
            intersected_ds = None
    masked_tpi_ds = None
