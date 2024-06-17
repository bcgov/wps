from datetime import datetime, timedelta
from typing import Generator
from app.jobs.common_model_fetchers import UnhandledPredictionModelType
from app.weather_models import ModelEnum

GRIB_LAYERS = ("TMP_TGL_2", "RH_TGL_2", "APCP_SFC_0", "WDIR_TGL_10", "WIND_TGL_10")
HRDPS_GRIB_LAYERS = ("TMP_AGL-2m", "APCP_Sfc", "WDIR_AGL-10m", "WIND_AGL-10m", "RH_AGL-2m")


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


def get_global_model_run_download_urls(now: datetime, model_run_hour: int) -> Generator[str, None, None]:
    """Yield urls to download GDPS (global) model runs"""

    # hh: model run start, in UTC [00, 12]
    # hhh: prediction hour [000, 003, 006, ..., 240]
    hh = f"{model_run_hour:02d}"
    # For the global model, we have prediction at 3 hour intervals up to 240 hours.
    for h in range(0, 241, 3):
        hhh = format(h, "03d")
        for level in GRIB_LAYERS:
            # Accumulated precipitation does not exist for 000 hour, so the url for this doesn't exist
            if hhh == "000" and level == "APCP_SFC_0":
                continue
            base_url = f"https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/{hh}/{hhh}/"
            date = get_file_date_part(now, model_run_hour)
            filename = f"CMC_glb_{level}_latlon.15x.15_{date}{hh}_P{hhh}.grib2"
            url = base_url + filename
            yield url


def get_high_res_model_run_download_urls(now: datetime, hour: int) -> Generator[str, None, None]:
    """Yield urls to download HRDPS (high-res) model runs"""
    hh = f"{hour:02d}"
    # For the high-res model, predictions are at 1 hour intervals up to 48 hours.
    for h in range(0, 49):
        hhh = format(h, "03d")
        for level in HRDPS_GRIB_LAYERS:
            # Accumulated precipitation does not exist for 000 hour, so the url for this doesn't exist
            if hhh == "000" and level == "APCP_Sfc":
                continue
            base_url = f"https://dd.weather.gc.ca/model_hrdps/continental/2.5km/{hh}/{hhh}/"
            date = get_file_date_part(now, hour, True)
            filename = f"{date}_MSC_HRDPS_{level}_RLatLon0.0225_PT{hhh}H.grib2"
            url = base_url + filename
            yield url


def get_regional_model_run_download_urls(now: datetime, hour: int, grib_layers: list[str] = GRIB_LAYERS, limit: int = 85) -> Generator[str, None, None]:
    """Yield urls to download RDPS model runs"""
    hh = f"{hour:02d}"
    # For the RDPS model, predictions are at 1 hour intervals up to 84 hours.
    for h in range(0, limit):
        hhh = format(h, "03d")
        for level in grib_layers:
            # Accumulated precipitation does not exist for 000 hour, so the url for this doesn't exist
            if hhh == "000" and level == "APCP_SFC_0":
                continue
            base_url = f"https://dd.weather.gc.ca/model_gem_regional/10km/grib2/{hh}/{hhh}/"
            date = get_file_date_part(now, hour)
            filename = f"CMC_reg_{level}_ps10km_{date}{hh}_P{hhh}.grib2"
            url = base_url + filename
            yield url


def get_model_run_urls(now: datetime, model_type: ModelEnum, model_run_hour: int):
    """Get model run url's"""
    if model_type == ModelEnum.GDPS:
        return list(get_global_model_run_download_urls(now, model_run_hour))
    if model_type == ModelEnum.HRDPS:
        return list(get_high_res_model_run_download_urls(now, model_run_hour))
    if model_type == ModelEnum.RDPS:
        return list(get_regional_model_run_download_urls(now, model_run_hour))
    raise UnhandledPredictionModelType()