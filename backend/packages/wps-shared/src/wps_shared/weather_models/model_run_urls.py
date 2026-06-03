from datetime import datetime
from typing import Generator, Iterable

from wps_shared.weather_models import ModelEnum, UnhandledPredictionModelType, get_file_date_part
from wps_shared.weather_models.gdps import GDPS_VARIABLE_NAMES
from wps_shared.weather_models.rdps import RDPS_VARIABLE_NAMES

GDPS_GRIB_LAYERS = tuple(GDPS_VARIABLE_NAMES.values())
RDPS_GRIB_LAYERS = tuple(RDPS_VARIABLE_NAMES.values())
HRDPS_GRIB_LAYERS = ("TMP_AGL-2m", "APCP_Sfc", "WDIR_AGL-10m", "WIND_AGL-10m", "RH_AGL-2m")


def get_global_model_run_download_urls(
    now: datetime, model_run_hour: int
) -> Generator[str, None, None]:
    """Yield urls to download GDPS (global) model runs"""

    # hh: model run start, in UTC [00, 12]
    # hhh: prediction hour [000, 003, 006, ..., 240]
    hh = f"{model_run_hour:02d}"
    # For the global model, we have prediction at 3 hour intervals up to 240 hours.
    for h in range(0, 241, 3):
        hhh = format(h, "03d")
        for level in GDPS_GRIB_LAYERS:
            # Accumulated precipitation does not exist for 000 hour, so the url for this doesn't exist
            if hhh == "000" and level == GDPS_VARIABLE_NAMES["precip"]:
                continue
            base_url = f"https://dd.weather.gc.ca/today/model_gdps/15km/{hh}/{hhh}/"
            date = get_file_date_part(now, model_run_hour)
            filename = f"{date}T{hh}Z_MSC_GDPS_{level}_LatLon0.15_PT{hhh}H.grib2"
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
            base_url = f"https://dd.weather.gc.ca/today/model_hrdps/continental/2.5km/{hh}/{hhh}/"
            date = get_file_date_part(now, hour, True)
            filename = f"{date}_MSC_HRDPS_{level}_RLatLon0.0225_PT{hhh}H.grib2"
            url = base_url + filename
            yield url


def get_regional_model_run_download_urls(
    now: datetime, hour: int, grib_layers: Iterable[str] = RDPS_GRIB_LAYERS, limit: int = 85
) -> Generator[str, None, None]:
    """Yield urls to download RDPS model runs from the new model_rdps path."""
    hh = f"{hour:02d}"
    for h in range(0, limit):
        hhh = format(h, "03d")
        for level in grib_layers:
            if hhh == "000" and level == RDPS_VARIABLE_NAMES["precip"]:
                continue
            base_url = f"https://dd.weather.gc.ca/today/model_rdps/10km/{hh}/{hhh}/"
            date = get_file_date_part(now, hour)
            filename = f"{date}T{hh}Z_MSC_RDPS_{level}_RLatLon0.09_PT{hhh}H.grib2"
            yield base_url + filename


def get_model_run_urls(now: datetime, model_type: ModelEnum, model_run_hour: int):
    """Get model run url's"""
    if model_type == ModelEnum.GDPS:
        return list(get_global_model_run_download_urls(now, model_run_hour))
    if model_type == ModelEnum.HRDPS:
        return list(get_high_res_model_run_download_urls(now, model_run_hour))
    if model_type == ModelEnum.RDPS:
        return list(get_regional_model_run_download_urls(now, model_run_hour))
    raise UnhandledPredictionModelType()
