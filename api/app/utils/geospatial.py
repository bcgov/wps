import os
from dataclasses import dataclass
import logging
from typing import Any, Optional
from aiobotocore.client import AioBaseClient
from botocore.exceptions import ClientError
from osgeo import gdal
import numpy as np

from app.db.database import DB_READ_STRING

logger = logging.getLogger(__name__)


@dataclass
class WarpOptions:
    """
    Inputs warping raster based on attributes from a source raster.
    """

    source_geotransform: Any
    source_projection: Any
    source_x_size: int
    source_y_size: int


@dataclass
class GeospatialOptions:
    """
    Options supplied by caller to declare optional outputs
    """

    warp_options: Optional[WarpOptions] = None
    include_geotransform: Optional[bool] = True
    include_projection: Optional[bool] = True
    include_x_size: Optional[bool] = None
    include_y_size: Optional[bool] = None


@dataclass
class GeospatialReadResult:
    """
    Raster data array and caller requested metadata
    """

    data_array: Any
    data_source: Any
    data_geotransform: Optional[Any]
    data_projection: Optional[Any]
    data_x_size: Optional[int]
    data_y_size: Optional[int]


def get_geospatial_metadata(data_source, options: Optional[GeospatialOptions]):
    """
    Extracts metadata defined by the options parameter from the data_source raster

    :param data_source: input raster to extract metadata from
    :param options: defines the metadata the caller is interested in extracting from the raster
    :return: optional metadata of geotransform, project, x and y sizes from the raster
    """
    geotransform = None
    projection = None
    x_size = None
    y_size = None
    if options is None:
        return (geotransform, projection, x_size, y_size)

    if options.include_geotransform:
        geotransform = data_source.GetGeoTransform()

    if options.include_projection:
        projection = data_source.GetProjection()

    if options.include_x_size:
        x_size = data_source.RasterXSize

    if options.include_y_size:
        y_size = data_source.RasterYSize

    return (geotransform, projection, x_size, y_size)


def read_raster_data(data_source, band=1):
    """
    Read raster data and return as array from the data source

    :param data_source: data source to read the data from
    :param band: the band from the data source to read from
    :return: raster data as array
    """
    data_band = data_source.GetRasterBand(band)
    data_array = data_band.ReadAsArray()
    return data_array


def get_raster_data(data_source, options: Optional[GeospatialOptions]) -> GeospatialReadResult:
    """
    Returns the raster data and optional metadata the caller is interested defined by the options parameter

    :param data_source: raster data source
    :param options: options defining the metadata the caller is interested in
    :return: raster data array and potential metadata
    """
    (data_geotransform, data_projection, data_x_size, data_y_size) = get_geospatial_metadata(data_source, options)
    data_array = read_raster_data(data_source)
    data_source = None
    return GeospatialReadResult(
        data_array=data_array, data_source=data_source, data_geotransform=data_geotransform, data_projection=data_projection, data_x_size=data_x_size, data_y_size=data_y_size
    )


def _get_raster_data_source(key: str, s3_data, options: Optional[GeospatialOptions]):
    """
    Retrieves geospatial file from S3. If the options include WarpOptions, it will warp
    the raster based on those options. If no WarpOptions are included,
    it simply read and return the raster data as is.

    :param key: the object store key pointing to the desired geospatial file
    :param s3_data: the object store content blob
    :param options: options defining the desired metadata as well as warp options if desired
    :return: raster data source
    """
    s3_data_mem_path = f"/vsimem/{key}"
    gdal.FileFromMemBuffer(s3_data_mem_path, s3_data)
    raster_ds = None
    if options is not None and options.warp_options is not None:
        raster_ds = gdal.Open(s3_data_mem_path, gdal.GA_ReadOnly)
        # peel off path, then extension, then attach .tif extension
        filename = ((key.split("/")[-1]).split(".")[0]) + ".tif"

        x_res = options.warp_options.source_geotransform[1]
        y_res = -options.warp_options.source_geotransform[5]
        minx = options.warp_options.source_geotransform[0]
        maxy = options.warp_options.source_geotransform[3]
        maxx = minx + options.warp_options.source_geotransform[1] * options.warp_options.source_x_size
        miny = maxy + options.warp_options.source_geotransform[5] * options.warp_options.source_y_size
        extent = [minx, miny, maxx, maxy]

        warped_mem_path = f"/vsimem/{filename}"

        # Warp to match input option parameters
        gdal.Warp(warped_mem_path, raster_ds, dstSRS=options.warp_options.source_projection, outputBounds=extent, xRes=x_res, yRes=y_res, resampleAlg=gdal.GRA_NearestNeighbour)
        output_raster_ds = gdal.Open(warped_mem_path, gdal.GA_ReadOnly)
        raster_ds = output_raster_ds
        gdal.Unlink(warped_mem_path)
    else:
        raster_ds = gdal.Open(s3_data_mem_path, gdal.GA_ReadOnly)

    gdal.Unlink(s3_data_mem_path)
    return raster_ds


async def read_raster_into_memory(client: AioBaseClient, bucket: str, key: str, options: Optional[GeospatialOptions]) -> Optional[GeospatialReadResult]:
    """
    Reads in the desired geospatial data as raw content bytes then returns the content as a data array and metadata
    defined by the options the caller is interested in.

    :param client: object store client
    :param bucket: the bucket the data is in
    :param key: the key identifying the geospatial data in the bucket
    :param options: options defining the desired metadata the user is interested in retrieving and vector
      options if the geospatial file is a vector file
    :return: raster data array and optional metadata
    """
    try:
        s3_source = await client.get_object(Bucket=bucket, Key=key)
        s3_data = await s3_source["Body"].read()
        data_source = _get_raster_data_source(key, s3_data, options)
        return get_raster_data(data_source, options)
    except ClientError as ex:
        if ex.response["Error"]["Code"] == "NoSuchKey":
            logger.info("No object found for key: %s", key)
            return None
        else:
            raise


def cut_raster_by_shape_id(advisory_shape_id: int, source_identifier: str, data_source: Any, options: Optional[GeospatialOptions]) -> GeospatialReadResult:
    """
    Given a raster dataset and a fire zone id, use gdal.Warp to clip out a fire zone from which we can retrieve stats.

    :param advisory_shape_id: The id of the fire zone (aka advisory_shape object) to clip with
    :param source_identifier: The source identifier of the fire zone.
    :param data_source: The source raster to be clipped.
    """
    output_path = f"/vsimem/firezone_{source_identifier}.tif"
    warp_options = gdal.WarpOptions(format="GTiff", cutlineDSName=DB_READ_STRING, cutlineSQL=f"SELECT geom FROM advisory_shapes WHERE id={advisory_shape_id}", cropToCutline=True)
    output_dataset = gdal.Warp(output_path, data_source, options=warp_options)
    return get_raster_data(output_dataset, options)


def data_array_to_raster(data_array: np.ndarray, key: str, options: GeospatialOptions, bands=1):
    output_driver = gdal.GetDriverByName("GTiff")
    mem_path = f"/vsimem/d2r-{key}"
    gdal.FileFromMemBuffer(mem_path, data_array)
    target_tiff = output_driver.Create(mem_path, xsize=options.warp_options.source_x_size, ysize=options.warp_options.source_y_size, bands=bands, eType=gdal.GDT_Byte)
    # Set the geotransform and projection to the same as the input.
    target_tiff.SetGeoTransform(options.warp_options.source_geotransform)
    target_tiff.SetProjection(options.warp_options.source_projection)

    # Write the classified data to the band.
    target_band = target_tiff.GetRasterBand(1)
    target_band.WriteArray(data_array)

    # Important to make sure data is flushed to disk!
    target_tiff.FlushCache()
    output_raster_ds = gdal.Open(mem_path, gdal.GA_ReadOnly)
    gdal.Unlink(mem_path)
    return output_raster_ds
