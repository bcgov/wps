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
from pydantic import BaseModel
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.run_type import RunType
from wps_shared.utils.s3_client import S3Client
from wps_shared.sfms.raster_addresser import FWIParameter
from app.routers.object_store_proxy import _proxy, read_object
from app.sfms.raster_addresser import RasterKeyAddresser

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/sfms/daily-fwi",
    tags=["SFMS Daily FWI"],
)

_addresser = RasterKeyAddresser()

_FOR_DATE_DESC = "Date of the raster (YYYY-MM-DD)"

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
    date: str
    parameter: str
    latitude: float
    longitude: float
    value: float | None



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


@router.get("/{for_date}/hffmc/value", response_model=FWIValueResponse, responses=_VALUE_RESPONSES)
async def get_hourly_ffmc_value_at_point(
    for_date: Annotated[date, Path(description=_FOR_DATE_DESC)],
    hour: Annotated[int, Query(ge=0, le=23, description="UTC hour (0-23)")],
    lat: Annotated[float, Query(ge=-90, le=90, description="Latitude in WGS84")],
    lon: Annotated[float, Query(ge=-180, le=180, description="Longitude in WGS84")],
):
    """Return the hourly FFMC raster value at a specific lat/lon coordinate."""
    datetime_utc = datetime(for_date.year, for_date.month, for_date.day, hour, tzinfo=timezone.utc)
    key = _addresser.get_calculated_hffmc_index_key(datetime_utc)
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
    "/{for_date}/{parameter}/value", response_model=FWIValueResponse, responses=_VALUE_RESPONSES
)
async def get_daily_fwi_value_at_point(
    for_date: Annotated[date, Path(description=_FOR_DATE_DESC)],
    parameter: Annotated[
        FWIParameter, Path(description="FWI parameter: dc, dmc, bui, ffmc, isi, fwi")
    ],
    lat: Annotated[float, Query(ge=-90, le=90, description="Latitude in WGS84")],
    lon: Annotated[float, Query(ge=-180, le=180, description="Longitude in WGS84")],
):
    """Return the daily FWI actuals raster value at a specific lat/lon coordinate."""
    key = _addresser.get_calculated_index_key(datetime(for_date.year, for_date.month, for_date.day, tzinfo=timezone.utc), parameter, RunType.ACTUAL)
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


@router.get("/{for_date}/hffmc", responses=_RASTER_RESPONSES)
async def get_hourly_ffmc_raster(
    request: Request,
    for_date: Annotated[date, Path(description=_FOR_DATE_DESC)],
    hour: Annotated[int, Query(ge=0, le=23, description="UTC hour (0-23)")],
):
    """Download the calculated hourly FFMC actuals raster for the given date and UTC hour."""
    datetime_utc = datetime(for_date.year, for_date.month, for_date.day, hour, tzinfo=timezone.utc)
    key = _addresser.get_calculated_hffmc_index_key(datetime_utc)
    logger.info("Streaming hourly FFMC raster: %s", key)
    return await _proxy(key, request.headers.get("range"), S3Client.stream_object)


@router.get("/{for_date}/{parameter}", responses=_RASTER_RESPONSES)
async def get_daily_fwi_raster(
    request: Request,
    for_date: Annotated[date, Path(description=_FOR_DATE_DESC)],
    parameter: Annotated[
        FWIParameter, Path(description="FWI parameter: dc, dmc, bui, ffmc, isi, fwi")
    ],
):
    """Download the daily FWI actuals raster for the given date and parameter."""
    key = _addresser.get_calculated_index_key(datetime(for_date.year, for_date.month, for_date.day, tzinfo=timezone.utc), parameter, RunType.ACTUAL)
    logger.info("Streaming daily FWI raster: %s", key)
    return await _proxy(key, request.headers.get("range"), S3Client.stream_object)
