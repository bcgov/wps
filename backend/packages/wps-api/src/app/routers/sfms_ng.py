"""daily raster downloads and point sampling for SFMS NG."""

import asyncio
import math
from datetime import date as Date
from datetime import datetime, time, timezone
from enum import StrEnum
from typing import Annotated, Literal

from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response
from pydantic import BaseModel, Field, ValidationError
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import (
    FBPParameter,
    FWIParameter,
    SFMSInterpolatedWeatherParameter,
)
from wps_shared.utils.s3_client import S3Client, get_s3_client

from app.routers.object_store_proxy import _proxy

router = APIRouter(prefix="/sfms/v1/daily", tags=["SFMS NG daily rasters"])
_addresser = SFMSNGRasterAddresser()


class DailyFWIParameter(StrEnum):
    FFMC = "ffmc"
    DMC = "dmc"
    DC = "dc"
    ISI = "isi"
    BUI = "bui"
    FWI = "fwi"
    DANGER_RATING = "danger_rating"


class DailyFBPParameter(StrEnum):
    SFC = "sfc"
    ROS = "ros"
    HFI = "hfi"
    TFC = "tfc"
    CFB = "cfb"
    FIRE_AREA_30MIN = "fire_area_30min"
    FMC = "fmc"


class DailyWeatherParameter(StrEnum):
    TEMPERATURE = "temperature"
    RELATIVE_HUMIDITY = "relative_humidity"
    WIND_SPEED = "wind_speed"
    WIND_DIRECTION = "wind_direction"
    PRECIPITATION = "precipitation"
    GRASS_CURING = "grass_curing"


DailyParameter = DailyFWIParameter | DailyFBPParameter | DailyWeatherParameter
SharedS3Client = Annotated[S3Client, Depends(get_s3_client)]
ForDate = Annotated[Date, Path(description="Target date of the raster", examples=["2026-10-13"])]
Latitude = Annotated[float, Query(ge=-90, le=90, description="Latitude in WGS84")]
Longitude = Annotated[float, Query(ge=-180, le=180, description="Longitude in WGS84")]
RequestedRunType = Annotated[
    RunType, Query(description="SFMS NG run type. Defaults to actual observations.")
]

_SOURCE_DESCRIPTION = """
Source system: SFMS NG. Select actuals or forecasts with `run_type`.
The date identifies the target day, not the time the forecast was issued.
Daily output rasters can be overwritten by later runs and are not an atomic snapshot.
FMC is shared by date across actual and forecast runs. Grass curing is the archived
input recorded by the latest successful run for the requested date and run type.
Grass curing is unavailable if that run has no recorded archived input.
"""
_DOWNLOAD_DESCRIPTION = (
    _SOURCE_DESCRIPTION
    + """
Download the original GeoTIFF. Supports HTTP range requests with a 206 response.
"""
)
_VALUE_DESCRIPTION = (
    _SOURCE_DESCRIPTION
    + """
Sample the raster at a WGS84 coordinate. Nodata and points outside the extent return
`value: null`. A 404 means the raster or required archived input is unavailable.
"""
)
_VALUES_DESCRIPTION = (
    _SOURCE_DESCRIPTION
    + """
Sample every parameter in this family at a WGS84 coordinate. Each parameter is null
on nodata or outside its raster extent. A missing required raster returns 404 for
the entire request.
"""
)
_ERROR_RESPONSES = {
    404: {"description": "Raster or required archived input not found"},
    422: {"description": "Invalid date, parameter, run type, or coordinates"},
    502: {"description": "Object store error or malformed run manifest"},
}
_RASTER_RESPONSES = {
    **_ERROR_RESPONSES,
    200: {"description": "GeoTIFF raster", "content": {"image/tiff": {}}},
    206: {"description": "GeoTIFF byte range", "content": {"image/tiff": {}}},
    403: {"description": "Object store denied access to the raster"},
}


class DailyPointResponse(BaseModel):
    date: Date = Field(description="Target date of the sampled rasters")
    run_type: RunType = Field(description="Requested SFMS NG run type")
    latitude: float = Field(description="Latitude supplied in the request")
    longitude: float = Field(description="Longitude supplied in the request")


class DailyValueResponse(DailyPointResponse):
    parameter: str = Field(description="Sampled parameter")
    value: float | None = Field(description="Raster value, or null on nodata or outside the extent")


class DailyFWIValuesResponse(DailyPointResponse):
    ffmc: float | None
    dmc: float | None
    dc: float | None
    isi: float | None
    bui: float | None
    fwi: float | None
    danger_rating: float | None


class DailyFBPValuesResponse(DailyPointResponse):
    sfc: float | None
    ros: float | None
    hfi: float | None
    tfc: float | None
    cfb: float | None
    fire_area_30min: float | None
    fmc: float | None


class DailyWeatherValuesResponse(DailyPointResponse):
    temperature: float | None
    relative_humidity: float | None
    wind_speed: float | None
    wind_direction: float | None
    precipitation: float | None
    grass_curing: float | None


class _ManifestInputs(BaseModel):
    static_rasters: dict[str, str] = Field(default_factory=dict)


class _RunManifest(BaseModel):
    # only parse the fields needed for reading, without constructing the pipeline's writer
    version: Literal[1]
    status: Literal["running", "success", "failed"]
    for_date: Date
    run_type: RunType
    input: _ManifestInputs = Field(default_factory=_ManifestInputs)


def _object_store_error(error: ClientError) -> HTTPException:
    code = error.response["Error"]["Code"]
    status = 404 if code in ("NoSuchKey", "404", "NotFound") else 502
    return HTTPException(status_code=status, detail=f"Object store error: {code}")


async def _read_object(s3_client: S3Client, key: str) -> bytes:
    try:
        return await s3_client.read_object(key)
    except ClientError as error:
        raise _object_store_error(error) from error


async def _grass_curing_key(s3_client: S3Client, for_date: Date, run_type: RunType) -> str:
    prefix = _addresser.get_run_manifest_prefix(run_type, for_date)
    try:
        keys = [key async for key in s3_client.iter_keys(prefix) if key.endswith(".json")]
    except ClientError as error:
        raise _object_store_error(error) from error

    # fixed width UTC filenames sort by run datetime, including across listing pages
    for key in sorted(keys, reverse=True):
        body = await _read_object(s3_client, key)
        try:
            manifest = _RunManifest.model_validate_json(body)
        except ValidationError as error:
            raise HTTPException(status_code=502, detail="Malformed SFMS NG run manifest") from error
        if manifest.for_date != for_date or manifest.run_type != run_type:
            raise HTTPException(
                status_code=502, detail="SFMS NG run manifest does not match its key"
            )
        if manifest.status != "success":
            continue
        grass_curing = manifest.input.static_rasters.get("grass_curing")
        if grass_curing:
            return grass_curing
        break

    raise HTTPException(status_code=404, detail="Archived grass curing input not found")


async def _raster_key(
    s3_client: S3Client, for_date: Date, parameter: DailyParameter, run_type: RunType
) -> str:
    target_datetime = datetime.combine(for_date, time(), tzinfo=timezone.utc)
    if parameter == DailyWeatherParameter.GRASS_CURING:
        return await _grass_curing_key(s3_client, for_date, run_type)
    if parameter == DailyFBPParameter.FMC:
        return _addresser.get_fmc_key(for_date)
    if parameter == DailyFWIParameter.DANGER_RATING:
        return _addresser.get_danger_rating_key(target_datetime, run_type)
    if isinstance(parameter, DailyFWIParameter):
        return _addresser.get_index_key(target_datetime, FWIParameter(parameter.value), run_type)
    if isinstance(parameter, DailyFBPParameter):
        return _addresser.get_fbp_key(target_datetime, FBPParameter(parameter.value), run_type)
    return _addresser.get_weather_key(
        target_datetime, SFMSInterpolatedWeatherParameter(parameter.value), run_type
    )


async def _sample_value(
    s3_client: S3Client,
    for_date: Date,
    parameter: DailyParameter,
    run_type: RunType,
    lat: float,
    lon: float,
) -> float | None:
    key = await _raster_key(s3_client, for_date, parameter, run_type)
    raster_bytes = await _read_object(s3_client, key)
    with WPSDataset.from_bytes(raster_bytes) as dataset:
        value = dataset.extract_value_at_point(lat, lon)
    return value if value is not None and math.isfinite(value) else None


async def _value_response(s3_client, for_date, parameter, run_type, lat, lon):
    value = await _sample_value(s3_client, for_date, parameter, run_type, lat, lon)
    return DailyValueResponse(
        date=for_date,
        run_type=run_type,
        parameter=parameter.value,
        latitude=lat,
        longitude=lon,
        value=value,
    )


async def _values_response(s3_client, for_date, parameters, run_type, lat, lon):
    values = await asyncio.gather(
        *(_sample_value(s3_client, for_date, p, run_type, lat, lon) for p in parameters)
    )
    return {
        "date": for_date,
        "run_type": run_type,
        "latitude": lat,
        "longitude": lon,
        **{parameter.value: value for parameter, value in zip(parameters, values)},
    }


async def _download_raster(request, s3_client, for_date, parameter, run_type):
    key = await _raster_key(s3_client, for_date, parameter, run_type)
    return await _proxy(key, request.headers.get("range"), s3_client.stream)


@router.get(
    "/fwi/{for_date}/values",
    response_model=DailyFWIValuesResponse,
    responses=_ERROR_RESPONSES,
    summary="Get all daily FWI values at a point",
    description=_VALUES_DESCRIPTION,
)
async def get_daily_fwi_values(
    for_date: ForDate,
    lat: Latitude,
    lon: Longitude,
    s3_client: SharedS3Client,
    run_type: RequestedRunType = RunType.ACTUAL,
):
    return await _values_response(s3_client, for_date, DailyFWIParameter, run_type, lat, lon)


@router.get(
    "/fbp/{for_date}/values",
    response_model=DailyFBPValuesResponse,
    responses=_ERROR_RESPONSES,
    summary="Get all daily FBP values at a point",
    description=_VALUES_DESCRIPTION,
)
async def get_daily_fbp_values(
    for_date: ForDate,
    lat: Latitude,
    lon: Longitude,
    s3_client: SharedS3Client,
    run_type: RequestedRunType = RunType.ACTUAL,
):
    return await _values_response(s3_client, for_date, DailyFBPParameter, run_type, lat, lon)


@router.get(
    "/weather/{for_date}/values",
    response_model=DailyWeatherValuesResponse,
    responses=_ERROR_RESPONSES,
    summary="Get all daily weather input values at a point",
    description=_VALUES_DESCRIPTION,
)
async def get_daily_weather_values(
    for_date: ForDate,
    lat: Latitude,
    lon: Longitude,
    s3_client: SharedS3Client,
    run_type: RequestedRunType = RunType.ACTUAL,
):
    return await _values_response(s3_client, for_date, DailyWeatherParameter, run_type, lat, lon)


@router.get(
    "/fwi/{for_date}/{parameter}/value",
    response_model=DailyValueResponse,
    responses=_ERROR_RESPONSES,
    summary="Get a daily FWI value at a point",
    description=_VALUE_DESCRIPTION,
)
async def get_daily_fwi_value(
    for_date: ForDate,
    parameter: DailyFWIParameter,
    lat: Latitude,
    lon: Longitude,
    s3_client: SharedS3Client,
    run_type: RequestedRunType = RunType.ACTUAL,
):
    return await _value_response(s3_client, for_date, parameter, run_type, lat, lon)


@router.get(
    "/fbp/{for_date}/{parameter}/value",
    response_model=DailyValueResponse,
    responses=_ERROR_RESPONSES,
    summary="Get a daily FBP value at a point",
    description=_VALUE_DESCRIPTION,
)
async def get_daily_fbp_value(
    for_date: ForDate,
    parameter: DailyFBPParameter,
    lat: Latitude,
    lon: Longitude,
    s3_client: SharedS3Client,
    run_type: RequestedRunType = RunType.ACTUAL,
):
    return await _value_response(s3_client, for_date, parameter, run_type, lat, lon)


@router.get(
    "/weather/{for_date}/{parameter}/value",
    response_model=DailyValueResponse,
    responses=_ERROR_RESPONSES,
    summary="Get a daily weather input value at a point",
    description=_VALUE_DESCRIPTION,
)
async def get_daily_weather_value(
    for_date: ForDate,
    parameter: DailyWeatherParameter,
    lat: Latitude,
    lon: Longitude,
    s3_client: SharedS3Client,
    run_type: RequestedRunType = RunType.ACTUAL,
):
    return await _value_response(s3_client, for_date, parameter, run_type, lat, lon)


@router.get(
    "/fwi/{for_date}/{parameter}",
    response_class=Response,
    responses=_RASTER_RESPONSES,
    summary="Download a daily FWI raster",
    description=_DOWNLOAD_DESCRIPTION,
)
async def get_daily_fwi_raster(
    request: Request,
    for_date: ForDate,
    parameter: DailyFWIParameter,
    s3_client: SharedS3Client,
    run_type: RequestedRunType = RunType.ACTUAL,
):
    return await _download_raster(request, s3_client, for_date, parameter, run_type)


@router.get(
    "/fbp/{for_date}/{parameter}",
    response_class=Response,
    responses=_RASTER_RESPONSES,
    summary="Download a daily FBP raster",
    description=_DOWNLOAD_DESCRIPTION,
)
async def get_daily_fbp_raster(
    request: Request,
    for_date: ForDate,
    parameter: DailyFBPParameter,
    s3_client: SharedS3Client,
    run_type: RequestedRunType = RunType.ACTUAL,
):
    return await _download_raster(request, s3_client, for_date, parameter, run_type)


@router.get(
    "/weather/{for_date}/{parameter}",
    response_class=Response,
    responses=_RASTER_RESPONSES,
    summary="Download a daily weather input raster",
    description=_DOWNLOAD_DESCRIPTION,
)
async def get_daily_weather_raster(
    request: Request,
    for_date: ForDate,
    parameter: DailyWeatherParameter,
    s3_client: SharedS3Client,
    run_type: RequestedRunType = RunType.ACTUAL,
):
    return await _download_raster(request, s3_client, for_date, parameter, run_type)
