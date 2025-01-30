import numpy as np
from osgeo import gdal, ogr, osr

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app import config
from app.auto_spatial_advisory.process_fuel_type_area import get_fuel_type_s3_key
from app.db.database import get_write_session_scope
from app.db.models.auto_spatial_advisory import Shape, TPIClassEnum, TPIFuelArea
from app.utils.geospatial import GDALResamplingMethod, warp_to_match_raster
from app.utils.s3 import set_s3_gdal_config


REPROJECTED_FUEL_LAYER_NAME = "warped_fuel.tif"
MASKED_TPI_NAME = "masked_tpi.tif"


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


def prepare_masked_tif():
    """
    Creates a masked TPI raster using a classified TPI raster from S3 storage and masking it using the fuel layer
    also from S3 storage
    """
    # Open up our rasters with gdal
    set_s3_gdal_config()
    bucket = config.get("OBJECT_STORE_BUCKET")
    tpi_raster_name = config.get("CLASSIFIED_TPI_DEM_NAME")
    fuel_raster_key = get_fuel_type_s3_key(bucket)
    tpi_raster_key = f"/vsis3/{bucket}/dem/tpi/{tpi_raster_name}"
    fuel_ds: gdal.Dataset = gdal.Open(fuel_raster_key, gdal.GA_ReadOnly)  # LCC projection
    tpi_ds: gdal.Dataset = gdal.Open(tpi_raster_key, gdal.GA_ReadOnly)  # BC Albers 3005 projection

    # Warp the fuel raster to match extent, spatial reference and cell size of the TPI raster
    warped_fuel_path = f"/vsimem/{REPROJECTED_FUEL_LAYER_NAME}"
    warped_fuel_ds: gdal.Dataset = warp_to_match_raster(fuel_ds, tpi_ds, warped_fuel_path, GDALResamplingMethod.NEAREST_NEIGHBOUR)

    # Convert the warped fuel dataset into a binary mask by classifying fuel cells as 1 and non-fuel cells as 0.
    warped_fuel_band: gdal.Band = warped_fuel_ds.GetRasterBand(1)
    warped_fuel_data: np.ndarray = warped_fuel_band.ReadAsArray()
    mask = np.where((warped_fuel_data > 0) & (warped_fuel_data < 99), 1, 0)

    # Some helpful things for creating the final masked TPI raster
    geo_transform = tpi_ds.GetGeoTransform()
    tpi_ds_srs = tpi_ds.GetProjection()
    tpi_band: gdal.Band = tpi_ds.GetRasterBand(1)
    tpi_data = tpi_band.ReadAsArray()

    # Apply the fuel layer mask to the classified TPI raster and store the result in an in-memory gdal dataset
    masked_tpi_data = np.multiply(mask, tpi_data)
    output_driver: gdal.Driver = gdal.GetDriverByName("MEM")
    masked_tpi_dataset: gdal.Dataset = output_driver.Create(f"/vsimem/{MASKED_TPI_NAME}", xsize=tpi_band.XSize, ysize=tpi_band.YSize, bands=1, eType=gdal.GDT_Byte)
    masked_tpi_dataset.SetGeoTransform(geo_transform)
    masked_tpi_dataset.SetProjection(tpi_ds_srs)
    masked_fuel_type_band: gdal.Band = masked_tpi_dataset.GetRasterBand(1)
    masked_fuel_type_band.SetNoDataValue(0)
    masked_fuel_type_band.WriteArray(masked_tpi_data)
    fuel_ds = None
    tpi_ds = None
    return masked_tpi_dataset


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
    masked_tpi_ds: gdal.Dataset = prepare_masked_tif()
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
