"""Typed raster dependency and output contracts for SFMS calculations."""

from dataclasses import dataclass
from datetime import date
from typing import Mapping

from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import (
    FWIParameter,
    GDALPath,
    S3Key,
    SFMSInterpolatedWeatherParameter,
)


@dataclass(frozen=True)
class FWIInputs:
    """Raster locations and metadata needed for one FWI calculation.

    `weather_keys` and `index_keys` values are GDAL paths for reading. `output_key` is a
    plain S3 key for writing.
    """

    weather_keys: Mapping[SFMSInterpolatedWeatherParameter, GDALPath]
    index_keys: Mapping[FWIParameter, GDALPath]
    output_key: S3Key
    run_type: RunType


@dataclass(frozen=True)
class SurfaceFuelConsumptionInputs:
    """Raster locations and metadata needed for one SFC calculation."""

    fuel_key: GDALPath
    ffmc_key: GDALPath
    bui_key: GDALPath
    percent_conifer_key: GDALPath
    output_key: S3Key
    run_type: RunType


@dataclass(frozen=True)
class FoliarMoistureContentInputs:
    """Static dependencies and date-specific outputs for shared daily FMC calculations."""

    elevation_key: GDALPath
    latitude_key: GDALPath
    longitude_key: GDALPath
    output_keys: Mapping[date, S3Key]
