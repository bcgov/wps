"""Daily FWI Raster Endpoints

Provides endpoints to download and query SFMS daily FWI actuals rasters
(FFMC, DMC, DC, ISI, FWI, BUI) and hourly FFMC rasters.

All endpoints require a valid bearer token (authentication_required).
"""

import logging
from datetime import date, datetime, timezone

from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, Path, Query, Request
from osgeo import osr
from pydantic import BaseModel
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import FWIParameter
from wps_shared.utils.s3_client import S3Client

from app.routers.object_store_proxy import _proxy
from app.sfms.raster_addresser import RasterKeyAddresser

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/sfms/daily-fwi",
    tags=["SFMS Daily FWI"],
)

_addresser = RasterKeyAddresser()


class FWIValueResponse(BaseModel):
    date: str
    parameter: str
    latitude: float
    longitude: float
    value: float | None


def _for_date_to_utc(for_date: date) -> datetime:
    return datetime(for_date.year, for_date.month, for_date.day, tzinfo=timezone.utc)


def _extract_value_at_point(ds: WPSDataset, lat: float, lon: float) -> float | None:
    """Extract the raster value at a WGS84 lat/lon coordinate."""
    gdal_ds = ds.as_gdal_ds()
    geotransform = gdal_ds.GetGeoTransform()
    projection = gdal_ds.GetProjection()

    src_srs = osr.SpatialReference()
    src_srs.ImportFromWkt(projection)
    src_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

    wgs84 = osr.SpatialReference()
    wgs84.ImportFromEPSG(4326)
    wgs84.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

    coord_transform = osr.CoordinateTransformation(wgs84, src_srs)
    x, y, _ = coord_transform.TransformPoint(lon, lat)

    x_origin, x_pixel_size = geotransform[0], geotransform[1]
    y_origin, y_pixel_size = geotransform[3], geotransform[5]

    col = int((x - x_origin) / x_pixel_size)
    row = int((y - y_origin) / y_pixel_size)

    if row < 0 or row >= gdal_ds.RasterYSize or col < 0 or col >= gdal_ds.RasterXSize:
        return None

    band = gdal_ds.GetRasterBand(1)
    nodata = band.GetNoDataValue()
    value = float(band.ReadAsArray(col, row, 1, 1)[0][0])

    if nodata is not None and value == nodata:
        return None

    return value


async def _read_raster_from_s3(key: str) -> bytes:
    """Download raw raster bytes from S3."""
    async with S3Client() as s3:
        try:
            response = await s3.client.get_object(Bucket=s3.bucket, Key=key)
            async with response["Body"] as stream:
                return await stream.read()
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "NoSuchKey":
                raise HTTPException(status_code=404, detail=f"Raster not found: {key}")
            raise HTTPException(status_code=502, detail=f"S3 error: {error_code}")


# /value routes must be defined before the bare download routes to avoid
# the variable {parameter} segment swallowing the literal "value" segment.


@router.get("/{for_date}/hffmc/value", response_model=FWIValueResponse)
async def get_hourly_ffmc_value_at_point(
    for_date: date = Path(..., description="Date of the raster (YYYY-MM-DD)"),
    hour: int = Query(..., ge=0, le=23, description="UTC hour (0-23)"),
    lat: float = Query(..., ge=-90, le=90, description="Latitude in WGS84"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude in WGS84"),
):
    """Return the hourly FFMC raster value at a specific lat/lon coordinate."""
    datetime_utc = datetime(for_date.year, for_date.month, for_date.day, hour, tzinfo=timezone.utc)
    key = _addresser.get_calculated_hffmc_index_key(datetime_utc)
    logger.info("Sampling hourly FFMC raster at (%s, %s) from %s", lat, lon, key)

    raster_bytes = await _read_raster_from_s3(key)
    ds = WPSDataset.from_bytes(raster_bytes)
    with ds:
        value = _extract_value_at_point(ds, lat, lon)

    return FWIValueResponse(
        date=for_date.isoformat(),
        parameter="hffmc",
        latitude=lat,
        longitude=lon,
        value=value,
    )


@router.get("/{for_date}/{parameter}/value", response_model=FWIValueResponse)
async def get_daily_fwi_value_at_point(
    for_date: date = Path(..., description="Date of the raster (YYYY-MM-DD)"),
    parameter: FWIParameter = Path(..., description="FWI parameter: dc, dmc, bui, ffmc, isi, fwi"),
    lat: float = Query(..., ge=-90, le=90, description="Latitude in WGS84"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude in WGS84"),
):
    """Return the daily FWI actuals raster value at a specific lat/lon coordinate."""
    key = _addresser.get_calculated_index_key(_for_date_to_utc(for_date), parameter, RunType.ACTUAL)
    logger.info("Sampling %s raster at (%s, %s) from %s", parameter.value, lat, lon, key)

    raster_bytes = await _read_raster_from_s3(key)
    ds = WPSDataset.from_bytes(raster_bytes)
    with ds:
        value = _extract_value_at_point(ds, lat, lon)

    return FWIValueResponse(
        date=for_date.isoformat(),
        parameter=parameter.value,
        latitude=lat,
        longitude=lon,
        value=value,
    )


@router.get("/{for_date}/hffmc")
async def get_hourly_ffmc_raster(
    request: Request,
    for_date: date = Path(..., description="Date of the raster (YYYY-MM-DD)"),
    hour: int = Query(..., ge=0, le=23, description="UTC hour (0-23)"),
):
    """Download the calculated hourly FFMC actuals raster for the given date and UTC hour."""
    datetime_utc = datetime(for_date.year, for_date.month, for_date.day, hour, tzinfo=timezone.utc)
    key = _addresser.get_calculated_hffmc_index_key(datetime_utc)
    logger.info("Streaming hourly FFMC raster: %s", key)
    return await _proxy(key, request.headers.get("range"), S3Client.stream_object)


@router.get("/{for_date}/{parameter}")
async def get_daily_fwi_raster(
    request: Request,
    for_date: date = Path(..., description="Date of the actuals raster (YYYY-MM-DD)"),
    parameter: FWIParameter = Path(..., description="FWI parameter: dc, dmc, bui, ffmc, isi, fwi"),
):
    """Download the daily FWI actuals raster for the given date and parameter."""
    key = _addresser.get_calculated_index_key(_for_date_to_utc(for_date), parameter, RunType.ACTUAL)
    logger.info("Streaming daily FWI raster: %s", key)
    return await _proxy(key, request.headers.get("range"), S3Client.stream_object)
