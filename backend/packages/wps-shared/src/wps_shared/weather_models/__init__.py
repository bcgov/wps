"""Code common to weather_models"""

import logging
import os
from datetime import datetime, timedelta
from enum import Enum

import requests

from wps_shared import config
from wps_shared.utils.redis import create_redis

logger = logging.getLogger(__name__)

# Key values on ModelRunGridSubsetPrediction.
# Wind direction (wdir_tgl_10_b) is handled slightly differently, so not included here.
SCALAR_MODEL_VALUE_KEYS = ("tmp_tgl_2", "rh_tgl_2", "wind_tgl_10")


class ModelEnum(str, Enum):
    """Enumerator for different kinds of supported weather models"""

    GDPS = "GDPS"
    RDPS = "RDPS"
    HRDPS = "HRDPS"
    GFS = "GFS"
    NAM = "NAM"
    ECMWF = "ECMWF"


class ProjectionEnum(str, Enum):
    """Enumerator for different projections based on the different
    kinds of weather models
    """

    LATLON_24X_24 = "latlon.24x.24"
    LATLON_15X_15 = "latlon.15x.15"
    HIGH_RES_CONTINENTAL = "ps2.5km"
    REGIONAL_PS = "ps10km"
    GFS_LONLAT = "lonlat.0.25deg"
    HRDPS_LATLON = "RLatLon0.0225"
    RDPS_LATLON = "RLatLon0.09"
    NAM_POLAR_STEREO = "ps32km"
    ECMWF_LATLON = "latlon.0.25deg"


def get_env_canada_model_run_hours(model_type: ModelEnum):
    """Yield model run hours for GDPS (00h00 and 12h00)"""
    if model_type == ModelEnum.GDPS:
        for hour in [0, 12]:
            yield hour
    elif model_type in (ModelEnum.HRDPS, ModelEnum.RDPS):
        for hour in [0, 6, 12, 18]:
            yield hour


def adjust_model_day(now: datetime, model_run_hour) -> datetime:
    """Adjust the model day, based on the current time.

    If now (e.g. 10h00) is less than model run (e.g. 12), it means we have to look for yesterdays
    model run.
    """
    if now.hour < model_run_hour:
        return now - timedelta(days=1)
    return now


def get_file_date_part(now, model_run_hour, is_hrdps: bool = False) -> str:
    """Construct the part of the filename that contains the model run date"""
    adjusted = adjust_model_day(now, model_run_hour)
    date = f"{adjusted.year}{adjusted.month:02d}{adjusted.day:02d}"
    if is_hrdps:
        date = date + f"T{model_run_hour:02d}Z"
    return date


class CompletedWithSomeExceptions(Exception):
    """Exception raised when processing completed, but there were some non critical exceptions"""


class NoFilesProcessed(Exception):
    """Exception raised when a model job completed but downloaded and processed zero files"""


class UnhandledPredictionModelType(Exception):
    """Exception raised when an unknown model type is encountered."""


def _filename_from_url(url: str, model_name: str) -> str:
    original = os.path.split(url)[-1]
    if model_name == "GFS":
        # NOTE: This is a very not-ideal way to interpolate the filename.
        # The original_filename that we get from the url is too long and must be condensed.
        # It also has multiple '.' chars in the URL that must be removed for the filename to be valid.
        # As long as NOAA's API remains unchanged, we'll have all the info we need (run datetimes,
        # projections, etc.) in the first 81 characters of original_filename.
        # An alternative would be to build out a regex to look for
        return original[:81].replace(".", "")
    return original


def download(
    url: str,
    path: str,
    config_cache_var: str,
    model_name: str,
    config_cache_expiry_var=None,
    fetcher=None,
) -> str | None:
    """
    Download a file from a url.
    NOTE: was using wget library initially, but has the drawback of not being able to control where the
    temporary files are stored. This is problematic, as giving the application write access to /app
    is a security concern.
    TODO: Would be nice to make this an async
    """
    target = os.path.join(os.getcwd(), path, _filename_from_url(url, model_name))

    cache = None
    cached_object = None
    if config.get(config_cache_var) == "True":
        cache = create_redis()
        try:
            cached_object = cache.get(url)
        except Exception as error:
            logger.exception(error)

    if cached_object:
        logger.info("Cache hit %s", url)
        with open(target, "wb") as file_object:
            file_object.write(cached_object)
        return target

    logger.warning("Downloading %s", url)
    if fetcher is not None:
        response = fetcher.get(url)
    else:
        raw = requests.get(url, timeout=60)
        if raw.status_code == 404:
            logger.info("404 error for %s", url)
            return None
        if raw.status_code != 200:
            raw.raise_for_status()
        response = raw

    if response is None:
        logger.info("404 for all candidates: %s", url)
        return None

    with open(target, "wb") as file_object:
        file_object.write(response.content)
    if cache:
        try:
            with open(target, "rb") as file_object:
                cache.set(url, file_object.read(), ex=config.get(config_cache_expiry_var, 21600))
        except Exception as error:
            logger.exception(error)
    return target
