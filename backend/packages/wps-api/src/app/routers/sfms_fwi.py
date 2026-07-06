"""Daily FWI Raster Endpoints

Provides endpoints to download and query SFMS daily FWI actuals rasters
(FFMC, DMC, DC, ISI, FWI, BUI) and hourly FFMC rasters.

Access is controlled by the APS Kong gateway (key-auth). Consumers register
for an API key at https://api.gov.bc.ca.
"""

import logging
from datetime import date, datetime, timezone
from typing import Annotated

from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, Path, Query, Request
from pydantic import BaseModel, Field
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.sfms.raster_addresser import FWIParameter
from wps_shared.utils.s3_client import S3Client
from wps_shared.utils.time import convert_utc_to_pdt

from app.routers.object_store_proxy import _proxy, read_object
from app.sfms.raster_addresser import RasterKeyAddresser

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/sfms/daily-fwi",
    tags=["SFMS Daily FWI"],
)

# Used for looking up the existing SFMS system run by geospatial, uploaded to
# sfms/uploads/* (RasterKeyAddresser.get_uploaded_index_key). Not either of the
# in-house calculation pipelines (sfms/calculated/* or sfms_ng/*), which are an in-progress
# own modernization effort and not yet the source of truth for this public API.
_addresser = RasterKeyAddresser()

_FOR_DATE_DESC = "Date of the raster (YYYY-MM-DD)"
_FOR_DATE_EXAMPLE = "2025-11-02"
_PARAMETER_DESC = "FWI parameter: dc, dmc, bui, ffmc, isi, fwi"
_LAT_DESC = "Latitude in WGS84"
_LON_DESC = "Longitude in WGS84"
_LAT_EXAMPLE = 49.0
_LON_EXAMPLE = -123.0
_HOUR_DESC = "UTC hour (0-23)"
_HOUR_EXAMPLE = 12

# 20:00 UTC is always the same calendar day in America/Vancouver time regardless of
# DST, matching the convention used elsewhere for addressing uploaded SFMS actuals
# (see daily_fwi_processor.py). get_uploaded_index_key converts to Pacific time
# internally, so passing midnight UTC would shift for_date back by one day.
_SFMS_SAFE_UTC_HOUR = 20


def _for_date_to_utc(for_date: date) -> datetime:
    return datetime(
        for_date.year, for_date.month, for_date.day, _SFMS_SAFE_UTC_HOUR, tzinfo=timezone.utc
    )


_RASTER_RESPONSES = {
    200: {"description": "GeoTIFF raster (full content)", "content": {"image/tiff": {}}},
    206: {
        "description": "GeoTIFF raster (partial content — range request)",
        "content": {"image/tiff": {}},
    },
    404: {"description": "Raster not found for the requested date and parameter"},
    422: {"description": "Invalid date, parameter, or hour value"},
    502: {"description": "Object store error"},
}

_VALUE_RESPONSES = {
    404: {"description": "Raster not found for the requested date and parameter"},
    422: {"description": "Invalid date, parameter, hour, or coordinate value"},
    502: {"description": "Object store error"},
}


class FWIValueResponse(BaseModel):
    date: str = Field(description="Date of the raster the value was sampled from (YYYY-MM-DD)")
    parameter: str = Field(
        description="FWI parameter that was sampled: dc, dmc, bui, ffmc, isi, fwi, or hffmc"
    )
    latitude: float = Field(description="Latitude of the sampled point, as provided in the request")
    longitude: float = Field(
        description="Longitude of the sampled point, as provided in the request"
    )
    value: float | None = Field(
        description="Sampled raster value, or null if the point is outside the raster's extent or falls on a nodata pixel"
    )


async def _load_raster(key: str) -> bytes:
    try:
        return await read_object(key)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchKey":
            raise HTTPException(status_code=404, detail=f"Raster not found: {key}")
        raise HTTPException(status_code=502, detail=f"S3 error: {error_code}")


# /value routes must be defined before the bare download routes to avoid
# the variable {parameter} segment swallowing the literal "value" segment.


@router.get(
    "/{for_date}/hffmc/value",
    response_model=FWIValueResponse,
    responses=_VALUE_RESPONSES,
    summary="Get hourly FFMC value at a point",
)
async def get_hourly_ffmc_value_at_point(
    for_date: Annotated[date, Path(description=_FOR_DATE_DESC, examples=[_FOR_DATE_EXAMPLE])],
    hour: Annotated[int, Query(ge=0, le=23, description=_HOUR_DESC, examples=[_HOUR_EXAMPLE])],
    lat: Annotated[float, Query(ge=-90, le=90, description=_LAT_DESC, examples=[_LAT_EXAMPLE])],
    lon: Annotated[float, Query(ge=-180, le=180, description=_LON_DESC, examples=[_LON_EXAMPLE])],
):
    """
    Sample the hourly FFMC (fine fuel moisture code) actuals raster at a single
    WGS84 lat/lon coordinate, for the given date and UTC hour.

    The raster returned is the actual raster uploaded by the existing/legacy SFMS system run by
    geospatial, not a WPS-calculated ones.

    Returns `value: null` if the coordinate falls outside the raster's extent or on
    a nodata pixel, rather than a 404 -- a 404 means the raster itself doesn't exist
    for that date/hour.
    """
    datetime_utc = datetime(for_date.year, for_date.month, for_date.day, hour, tzinfo=timezone.utc)
    datetime_pdt = convert_utc_to_pdt(datetime_utc)
    hour_suffix = f"{datetime_pdt.hour:02d}.tif"
    async with S3Client() as s3_client:
        response = await s3_client.client.list_objects_v2(
            Bucket=s3_client.bucket,
            Prefix=f"sfms/uploads/hourlies/{datetime_pdt.date().isoformat()}",
        )
    key = next(
        (obj["Key"] for obj in response.get("Contents", []) if obj["Key"].endswith(hour_suffix)),
        None,
    )
    if key is None:
        raise HTTPException(
            status_code=404, detail=f"No hFFMC raster found for {for_date} hour {hour}"
        )
    logger.info("Sampling hourly FFMC raster at (%s, %s) from %s", lat, lon, key)

    raster_bytes = await _load_raster(key)
    ds = WPSDataset.from_bytes(raster_bytes)
    with ds:
        value = ds.extract_value_at_point(lat, lon)

    return FWIValueResponse(
        date=for_date.isoformat(),
        parameter="hffmc",
        latitude=lat,
        longitude=lon,
        value=value,
    )


@router.get(
    "/{for_date}/{parameter}/value",
    response_model=FWIValueResponse,
    responses=_VALUE_RESPONSES,
    summary="Get daily FWI value at a point",
)
async def get_daily_fwi_value_at_point(
    for_date: Annotated[date, Path(description=_FOR_DATE_DESC, examples=[_FOR_DATE_EXAMPLE])],
    parameter: Annotated[FWIParameter, Path(description=_PARAMETER_DESC, examples=["ffmc"])],
    lat: Annotated[float, Query(ge=-90, le=90, description=_LAT_DESC, examples=[_LAT_EXAMPLE])],
    lon: Annotated[float, Query(ge=-180, le=180, description=_LON_DESC, examples=[_LON_EXAMPLE])],
):
    """
    Sample the daily FWI actuals raster at a single WGS84 lat/lon coordinate, for
    the given date and parameter (dc, dmc, bui, ffmc, isi, or fwi).

    Returns `value: null` if the coordinate falls outside the raster's extent or on
    a nodata pixel, rather than a 404 -- a 404 means the raster itself doesn't exist
    for that date/parameter.
    """
    key = _addresser.get_uploaded_index_key(_for_date_to_utc(for_date), parameter)
    logger.info("Sampling %s raster at (%s, %s) from %s", parameter.value, lat, lon, key)

    raster_bytes = await _load_raster(key)
    ds = WPSDataset.from_bytes(raster_bytes)
    with ds:
        value = ds.extract_value_at_point(lat, lon)

    return FWIValueResponse(
        date=for_date.isoformat(),
        parameter=parameter.value,
        latitude=lat,
        longitude=lon,
        value=value,
    )


@router.get(
    "/{for_date}/hffmc",
    responses=_RASTER_RESPONSES,
    summary="Download hourly FFMC raster",
)
async def get_hourly_ffmc_raster(
    request: Request,
    for_date: Annotated[date, Path(description=_FOR_DATE_DESC, examples=[_FOR_DATE_EXAMPLE])],
    hour: Annotated[int, Query(ge=0, le=23, description=_HOUR_DESC, examples=[_HOUR_EXAMPLE])],
):
    """
    Download the hourly FFMC (fine fuel moisture code) actuals raster, as a
    GeoTIFF, for the given date and UTC hour.

    The raster returned is the actual raster uploaded by the existing/legacy SFMS system run by
    geospatial, not a WPS-calculated ones.

    Supports HTTP range requests (a `Range` header returns a 206 partial response).
    """
    datetime_utc = datetime(for_date.year, for_date.month, for_date.day, hour, tzinfo=timezone.utc)
    datetime_pdt = convert_utc_to_pdt(datetime_utc)
    hour_suffix = f"{datetime_pdt.hour:02d}.tif"
    async with S3Client() as s3_client:
        response = await s3_client.client.list_objects_v2(
            Bucket=s3_client.bucket,
            Prefix=f"sfms/uploads/hourlies/{datetime_pdt.date().isoformat()}",
        )
    key = next(
        (obj["Key"] for obj in response.get("Contents", []) if obj["Key"].endswith(hour_suffix)),
        None,
    )
    if key is None:
        raise HTTPException(
            status_code=404, detail=f"No hFFMC raster found for {for_date} hour {hour}"
        )
    logger.info("Streaming hourly FFMC raster: %s", key)
    return await _proxy(key, request.headers.get("range"), S3Client.stream_object)


@router.get(
    "/{for_date}/{parameter}",
    responses=_RASTER_RESPONSES,
    summary="Download daily FWI raster",
)
async def get_daily_fwi_raster(
    request: Request,
    for_date: Annotated[date, Path(description=_FOR_DATE_DESC, examples=[_FOR_DATE_EXAMPLE])],
    parameter: Annotated[FWIParameter, Path(description=_PARAMETER_DESC, examples=["ffmc"])],
):
    """
    Download the daily FWI actuals raster for the given date and
    parameter (dc, dmc, bui, ffmc, isi, or fwi).

    The raster returned is the actual raster uploaded by the existing/legacy SFMS system run by
    geospatial.

    Supports HTTP range requests (a `Range` header returns a 206 partial response).
    """
    key = _addresser.get_uploaded_index_key(_for_date_to_utc(for_date), parameter)
    logger.info("Streaming daily FWI raster: %s", key)
    return await _proxy(key, request.headers.get("range"), S3Client.stream_object)
