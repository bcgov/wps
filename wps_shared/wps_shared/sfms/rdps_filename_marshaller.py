"""
Reading and writing of RDPS URLs, based on the specification here:
https://eccc-msc.github.io/open-data/msc-data/nwp_rdps/readme_rdps-datamart_en/#filename-nomenclature
"""

from datetime import datetime
import enum
from typing import Literal
from dataclasses import dataclass


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


def parse_rdps_filename(url: str):
    """Parse and return the forecast start date and run hour from the RDPS grib url."""
    tokens = url.split(DELIMITER)
    assert tokens[0] in [SourcePrefix.CMC.value, SourcePrefix.COMPUTED.value]
    assert tokens[1] == REG
    assert tokens[2] == APCP
    assert tokens[3] == SFC
    assert tokens[4] == LEVEL
    assert tokens[5] == PS10KM

    # utc datetime in YYYYMMDDHH format
    assert len(tokens[6]) == 10
    forecast_start_date = tokens[6][:-2]
    run_hour = tokens[6][-2:]
    assert run_hour in RUN_HOURS

    # forecast hour and grib2 file ext
    assert len(tokens[7]) == 10
    final_tokens = tokens[7].split(".")
    assert len(final_tokens) == 2
    # strip off constant 'P', get forecast hours triplet
    forecast_hour = final_tokens[0][-3:]
    assert forecast_hour in FORECAST_HOURS

    return (forecast_start_date, run_hour, forecast_hour)


def check_compose_invariants(forecast_start_date: datetime, run_hour: int, forecast_hour: int, weather_parameter: str):
    """Explode if any of these assertions fail"""
    assert forecast_start_date.tzinfo is not None
    assert int(forecast_start_date.utcoffset().total_seconds()) == 0
    assert f"{forecast_hour:03d}" in FORECAST_HOURS
    assert run_hour in list(range(0, 36))
    assert weather_parameter in weather_key_parameters


def compose_rdps_filename(forecast_start_date: datetime, run_hour: int, forecast_hour: int, weather_parameter: str):
    """Compose and return a computed RDPS url given a forecast start date, run hour and forecast hour."""
    check_compose_invariants(forecast_start_date, run_hour, forecast_hour, weather_parameter)
    key_params = get_weather_key_params(weather_parameter)
    model_hour = model_run_for_hour(run_hour)
    adjusted_forecast_hour = adjust_forecast_hour(run_hour, forecast_hour)
    file_ext = ".grib2"

    return (
        f"{SourcePrefix.CMC.value}{DELIMITER}{REG}{DELIMITER}{key_params.variable}{DELIMITER}{key_params.level_type}{DELIMITER}{key_params.level}{DELIMITER}{PS10KM}{DELIMITER}"
        f"{forecast_start_date.date().isoformat().replace('-', '')}{model_hour:02d}{DELIMITER}P{adjusted_forecast_hour:03d}{file_ext}"
    )


def compose_rdps_key(forecast_start_date: datetime, run_hour: int, forecast_hour: int, weather_parameter: str):
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


def compose_rdps_filename_hffmc(model_run_start: datetime, offset_hour: int, weather_parameter: str):
    key_params = get_weather_key_params(weather_parameter)
    file_ext = ".grib2"
    return (
        f"{SourcePrefix.CMC.value}{DELIMITER}{REG}{DELIMITER}{key_params.variable}{DELIMITER}{key_params.level_type}{DELIMITER}{key_params.level}{DELIMITER}{PS10KM}{DELIMITER}"
        f"{model_run_start.date().isoformat().replace('-', '')}{model_run_start.hour:02d}{DELIMITER}P{offset_hour:03d}{file_ext}"
    )
