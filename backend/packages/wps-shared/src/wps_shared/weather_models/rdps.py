# backend/packages/wps-shared/src/wps_shared/weather_models/rdps.py
"""Single source of truth for RDPS URL building, filename construction, and parsing."""

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Generator, Literal

from wps_shared.weather_models import ProjectionEnum, get_file_date_part

RDPS_GRIB_LAYERS = ("TMP_AGL-2m", "RH_AGL-2m", "APCP_Sfc", "WDIR_AGL-10m", "WIND_AGL-10m")
GRIB_LAYERS = RDPS_GRIB_LAYERS  # backward-compat alias

# Named mapping used by the SFMS download job
SFMS_GRIB_LAYERS = {
    "temp": "TMP_AGL-2m",
    "rh": "RH_AGL-2m",
    "precip": "APCP_Sfc",
    "wind_speed": "WIND_AGL-10m",
}


def get_regional_model_run_download_urls(
    now: datetime, hour: int, grib_layers: tuple = RDPS_GRIB_LAYERS, limit: int = 85
) -> Generator[str, None, None]:
    """Yield urls to download RDPS model runs from the new model_rdps path."""
    hh = f"{hour:02d}"
    for h in range(0, limit):
        hhh = format(h, "03d")
        for level in grib_layers:
            if hhh == "000" and level == "APCP_Sfc":
                continue
            base_url = f"https://dd.weather.gc.ca/today/model_rdps/10km/{hh}/{hhh}/"
            date = get_file_date_part(now, hour)
            filename = f"{date}T{hh}Z_MSC_RDPS_{level}_RLatLon0.09_PT{hhh}H.grib2"
            yield base_url + filename


def parse_rdps_msc_filename(url: str):
    """Parse the new MSC RDPS filename format.

    Expected filename: {YYYYMMDD}T{HH}Z_MSC_RDPS_{VAR_LEVEL}_RLatLon0.09_PT{hhh}H.grib2
    Example: 20260501T12Z_MSC_RDPS_TMP_AGL-2m_RLatLon0.09_PT003H.grib2
    Returns: (variable_name, ProjectionEnum.RDPS_LATLON, model_run_timestamp, prediction_timestamp)
    """
    import datetime as _dt
    import os

    basename = os.path.basename(url)
    parts = basename.split("_")
    # parts[0] = "20260501T12Z", parts[1] = "MSC", parts[2] = "RDPS"
    if len(parts) < 6 or parts[1] != "MSC" or parts[2] != "RDPS":
        raise ValueError(f"Not a valid MSC RDPS filename: {basename}")

    date_run = parts[0]  # e.g. "20260501T12Z"
    if len(date_run) != 12 or "T" not in date_run:
        raise ValueError(f"Cannot parse date/run from: {date_run}")

    date_str = date_run[:8]  # "20260501"
    run_hour = int(date_run[9:11])  # 12

    model_run_timestamp = _dt.datetime(
        year=int(date_str[:4]),
        month=int(date_str[4:6]),
        day=int(date_str[6:8]),
        hour=run_hour,
        tzinfo=_dt.timezone.utc,
    )

    # Variable name: everything between "_RDPS_" and "_RLatLon"
    after_rdps = basename[basename.index("_RDPS_") + 6 :]
    variable_name = after_rdps[: after_rdps.index("_RLatLon")]

    # Forecast hour from last part: "PT003H.grib2" -> 3
    pt_part = parts[-1].split(".")[0]  # "PT003H"
    if not pt_part.startswith("PT") or not pt_part.endswith("H"):
        raise ValueError(f"Cannot parse forecast hour from: {pt_part}")
    forecast_hours = int(pt_part[2:-1])
    prediction_timestamp = model_run_timestamp + _dt.timedelta(hours=forecast_hours)

    return variable_name, ProjectionEnum.RDPS_LATLON, model_run_timestamp, prediction_timestamp


class SourcePrefix(enum.Enum):
    COMPUTED = "COMPUTED"  # Computed constant, indicating that the result file is computed by wps
    CMC = "CMC"  # Canadian Meterological Centre constant


# RDPS constant
REG = "reg"
# Accumulating precipitation constant
APCP = "APCP"
# Surface level type
SFC = "SFC"
# Level 0
LEVEL = "0"
# Polar-stereographic projection at 10km resolution
PS10KM = "ps10km"
# Grib2 file type
GRIB2 = "grib2"
# Filename delimiter
DELIMITER = "_"
# Possible run hours
RUN_HOURS = ["00", "12"]
# Possible forecast hours
FORECAST_HOURS = [f"{hour:03d}" for hour in list(range(0, 84))]


@dataclass(frozen=True)
class WeatherModelKeyParams:
    variable: str
    level_type: str
    level: str


weather_key_parameters = {
    "temp": WeatherModelKeyParams("TMP", "TGL", "2"),
    "precip": WeatherModelKeyParams("APCP", "SFC", "0"),
    "wind_speed": WeatherModelKeyParams("WIND", "TGL", "10"),
    "rh": WeatherModelKeyParams("RH", "TGL", "2"),
}

# New MSC variable names for SFMS parameters
_NEW_VARIABLE_NAMES = {
    "temp": "TMP_AGL-2m",
    "rh": "RH_AGL-2m",
    "precip": "APCP_Sfc",
    "wind_speed": "WIND_AGL-10m",
}


def get_weather_key_params(parameter):
    return weather_key_parameters.get(parameter, None)



def model_run_for_hour(hour: int) -> Literal[0, 12]:
    """Returns the model run the hour is for based on when the latest model ran."""
    return 0 if hour < 12 else 12


def adjust_forecast_hour(run_hour: int, forecast_hour: int):
    """
    Adjust the forecast hour given the run hour so return an offset from the run hour.

    :param run_hour: hour the model was run at
    :param forecast_hour: the hour the forecast is for
    :return: the adjusted hour
    """
    model_hour = model_run_for_hour(run_hour)
    return forecast_hour - model_hour


def check_compose_invariants(
    forecast_start_date: datetime, run_hour: int, forecast_hour: int, weather_parameter: str
):
    """Explode if any of these assertions fail"""
    assert forecast_start_date.tzinfo is not None
    assert int(forecast_start_date.utcoffset().total_seconds()) == 0
    assert f"{forecast_hour:03d}" in FORECAST_HOURS
    assert run_hour in list(range(0, 36))
    assert weather_parameter in weather_key_parameters


def compose_rdps_filename(
    forecast_start_date: datetime, run_hour: int, forecast_hour: int, weather_parameter: str
):
    """Compose RDPS S3 filename in new MSC format."""
    check_compose_invariants(forecast_start_date, run_hour, forecast_hour, weather_parameter)
    assert weather_parameter in _NEW_VARIABLE_NAMES, f"Unknown weather parameter: {weather_parameter}"
    model_hour = model_run_for_hour(run_hour)
    adjusted_forecast_hour = adjust_forecast_hour(run_hour, forecast_hour)
    variable = _NEW_VARIABLE_NAMES[weather_parameter]
    date_str = forecast_start_date.date().isoformat().replace("-", "")
    return f"{date_str}T{model_hour:02d}Z_MSC_RDPS_{variable}_RLatLon0.09_PT{adjusted_forecast_hour:03d}H.grib2"


def compose_rdps_key(
    forecast_start_date: datetime, run_hour: int, forecast_hour: int, weather_parameter: str
):
    """Compose and return a computed RDPS url given a forecast start date, run hour and forecast hour."""
    model_hour = model_run_for_hour(run_hour)
    return f"{model_hour:02d}/{weather_parameter}/{compose_rdps_filename(forecast_start_date, run_hour, forecast_hour, weather_parameter)}"


def compose_computed_rdps_filename(accumulation_end_datetime: datetime) -> str:
    """
    Compose and return a computed RDPS url given the datetime that precip is being accumulated to.
    For details on weather model naming conventions, see: https://github.com/bcgov/wps/tree/main/api/app/weather_models/weather-model-naming.md
    """
    key_params = get_weather_key_params("precip")
    file_ext = ".tif"

    return (
        f"{SourcePrefix.COMPUTED.value}{DELIMITER}{REG}{DELIMITER}{key_params.variable}{DELIMITER}{key_params.level_type}{DELIMITER}{key_params.level}{DELIMITER}{PS10KM}{DELIMITER}"
        f"{accumulation_end_datetime.strftime(f'%Y%m%d{DELIMITER}%Hz')}{file_ext}"
    )


def compose_computed_precip_rdps_key(accumulation_end_datetime: datetime):
    """Compose and return a computed RDPS url given the datetime that precip is being accumulated to."""
    model_hour = model_run_for_hour(accumulation_end_datetime.hour)
    return f"{model_hour:02d}/precip/{compose_computed_rdps_filename(accumulation_end_datetime)}"


def compose_rdps_key_hffmc(model_run_start: datetime, offset_hour: int, weather_parameter: str):
    """Compose and return a computed RDPS url given a forecast start date and hour offset."""
    model_hour = model_run_for_hour(model_run_start.hour)
    return f"{model_hour:02d}/{weather_parameter}/{compose_rdps_filename_hffmc(model_run_start, offset_hour, weather_parameter)}"


def compose_rdps_filename_hffmc(
    model_run_start: datetime, offset_hour: int, weather_parameter: str
):
    """Compose RDPS hffmc S3 filename in new MSC format."""
    assert weather_parameter in _NEW_VARIABLE_NAMES, f"Unknown weather parameter: {weather_parameter}"
    variable = _NEW_VARIABLE_NAMES[weather_parameter]
    date_str = model_run_start.date().isoformat().replace("-", "")
    return f"{date_str}T{model_run_start.hour:02d}Z_MSC_RDPS_{variable}_RLatLon0.09_PT{offset_hour:03d}H.grib2"


def compose_rdps_key_legacy(
    forecast_start_date: datetime, run_hour: int, forecast_hour: int, weather_parameter: str
):
    """Compose S3 key using the old CMC_reg format. Read-only fallback during 7-day transition."""
    check_compose_invariants(forecast_start_date, run_hour, forecast_hour, weather_parameter)
    key_params = get_weather_key_params(weather_parameter)
    model_hour = model_run_for_hour(run_hour)
    adjusted_forecast_hour = adjust_forecast_hour(run_hour, forecast_hour)
    date_str = forecast_start_date.date().isoformat().replace("-", "")
    filename = (
        f"{SourcePrefix.CMC.value}{DELIMITER}{REG}{DELIMITER}{key_params.variable}{DELIMITER}"
        f"{key_params.level_type}{DELIMITER}{key_params.level}{DELIMITER}{PS10KM}{DELIMITER}"
        f"{date_str}{model_hour:02d}{DELIMITER}P{adjusted_forecast_hour:03d}.grib2"
    )
    return f"{model_hour:02d}/{weather_parameter}/{filename}"


def compose_rdps_key_hffmc_legacy(
    model_run_start: datetime, offset_hour: int, weather_parameter: str
):
    """Compose hffmc S3 key using old CMC_reg format. Read-only fallback during 7-day transition."""
    key_params = get_weather_key_params(weather_parameter)
    model_hour = model_run_for_hour(model_run_start.hour)
    date_str = model_run_start.date().isoformat().replace("-", "")
    filename = (
        f"{SourcePrefix.CMC.value}{DELIMITER}{REG}{DELIMITER}{key_params.variable}{DELIMITER}"
        f"{key_params.level_type}{DELIMITER}{key_params.level}{DELIMITER}{PS10KM}{DELIMITER}"
        f"{date_str}{model_run_start.hour:02d}{DELIMITER}P{offset_hour:03d}.grib2"
    )
    return f"{model_hour:02d}/{weather_parameter}/{filename}"
