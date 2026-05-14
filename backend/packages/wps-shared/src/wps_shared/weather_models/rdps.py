# backend/packages/wps-shared/src/wps_shared/weather_models/rdps.py
"""Single source of truth for RDPS object store key and file name construction and RDPS variable definitions."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from wps_shared.weather_models import ProjectionEnum

RDPS_VARIABLE_NAMES = {
    "temp": "AirTemp_AGL-2m",
    "rh": "RelativeHumidity_AGL-2m",
    "precip": "Precip-Accum_Sfc",
    "wind_speed": "WindSpeed_AGL-10m",
    "wind_dir": "WindDir_AGL-10m",
}


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


@dataclass(frozen=True)
class WeatherModelKeyParams:
    variable: str
    level_type: str
    level: str


class RDPSKeyAddresser:
    """Composes S3 keys and filenames for RDPS grib2 and derived raster files."""

    # Legacy RDPS constant
    REG = "reg"
    # Legacy Filename delimiter
    DELIMITER = "_"
    # Possible forecast hours
    FORECAST_HOURS = [f"{hour:03d}" for hour in list(range(0, 84))]
    # Computed constant, indicating that the result file is computed by wps
    COMPUTED = "COMPUTED"
    # Legacy Canadian Meterological Centre constant
    CMC = "CMC"

    weather_key_parameters = {
        "temp": WeatherModelKeyParams("TMP", "TGL", "2"),
        "precip": WeatherModelKeyParams("APCP", "SFC", "0"),
        "wind_speed": WeatherModelKeyParams("WIND", "TGL", "10"),
        "rh": WeatherModelKeyParams("RH", "TGL", "2"),
    }

    def _check_compose_invariants(
        self,
        forecast_start_date: datetime,
        run_hour: int,
        forecast_hour: int,
        weather_parameter: str,
    ):
        """Explode if any of these assertions fail."""
        assert forecast_start_date.tzinfo is not None
        utc_offset = forecast_start_date.utcoffset()
        assert utc_offset is not None and int(utc_offset.total_seconds()) == 0
        assert f"{forecast_hour:03d}" in self.FORECAST_HOURS
        assert run_hour in list(range(0, 36))
        assert weather_parameter in self.weather_key_parameters

    def compose_rdps_key(
        self,
        forecast_start_date: datetime,
        run_hour: int,
        forecast_hour: int,
        weather_parameter: str,
    ) -> str:
        """Compose and return an RDPS S3 key given a forecast start date, run hour and forecast hour."""
        model_hour = model_run_for_hour(run_hour)
        return f"{model_hour:02d}/{weather_parameter}/{self._compose_rdps_filename(forecast_start_date, run_hour, forecast_hour, weather_parameter)}"

    def compose_computed_precip_rdps_key(self, accumulation_end_datetime: datetime) -> str:
        """Compose and return a computed RDPS key for the datetime that precip is being accumulated to."""
        model_hour = model_run_for_hour(accumulation_end_datetime.hour)
        return f"{model_hour:02d}/precip/{self._compose_computed_rdps_filename(accumulation_end_datetime)}"

    def compose_rdps_key_hffmc(
        self, model_run_start: datetime, offset_hour: int, weather_parameter: str
    ) -> str:
        """Compose and return an RDPS S3 key given a model run start date and hour offset."""
        model_hour = model_run_for_hour(model_run_start.hour)
        return f"{model_hour:02d}/{weather_parameter}/{self._compose_rdps_filename_hffmc(model_run_start, offset_hour, weather_parameter)}"

    def compose_rdps_key_legacy(
        self,
        forecast_start_date: datetime,
        run_hour: int,
        forecast_hour: int,
        weather_parameter: str,
    ) -> str:
        """Compose S3 key using the old CMC_reg format. Read-only fallback during 7-day transition."""
        self._check_compose_invariants(
            forecast_start_date, run_hour, forecast_hour, weather_parameter
        )
        key_params = self.weather_key_parameters[weather_parameter]
        model_hour = model_run_for_hour(run_hour)
        adjusted_forecast_hour = adjust_forecast_hour(run_hour, forecast_hour)
        date_str = forecast_start_date.date().isoformat().replace("-", "")
        filename = (
            f"{self.CMC}{self.DELIMITER}{self.REG}{self.DELIMITER}{key_params.variable}{self.DELIMITER}"
            f"{key_params.level_type}{self.DELIMITER}{key_params.level}{self.DELIMITER}{ProjectionEnum.REGIONAL_PS.value}{self.DELIMITER}"
            f"{date_str}{model_hour:02d}{self.DELIMITER}P{adjusted_forecast_hour:03d}.grib2"
        )
        return f"{model_hour:02d}/{weather_parameter}/{filename}"

    def compose_rdps_key_hffmc_legacy(
        self, model_run_start: datetime, offset_hour: int, weather_parameter: str
    ) -> str:
        """Compose hffmc S3 key using old CMC_reg format. Read-only fallback during 7-day transition."""
        key_params = self.weather_key_parameters[weather_parameter]
        model_hour = model_run_for_hour(model_run_start.hour)
        date_str = model_run_start.date().isoformat().replace("-", "")
        filename = (
            f"{self.CMC}{self.DELIMITER}{self.REG}{self.DELIMITER}{key_params.variable}{self.DELIMITER}"
            f"{key_params.level_type}{self.DELIMITER}{key_params.level}{self.DELIMITER}{ProjectionEnum.REGIONAL_PS.value}{self.DELIMITER}"
            f"{date_str}{model_run_start.hour:02d}{self.DELIMITER}P{offset_hour:03d}.grib2"
        )
        return f"{model_hour:02d}/{weather_parameter}/{filename}"

    def _compose_rdps_filename(
        self,
        forecast_start_date: datetime,
        run_hour: int,
        forecast_hour: int,
        weather_parameter: str,
    ) -> str:
        """Compose RDPS S3 filename in new MSC format."""
        self._check_compose_invariants(
            forecast_start_date, run_hour, forecast_hour, weather_parameter
        )
        assert weather_parameter in RDPS_VARIABLE_NAMES, (
            f"Unknown weather parameter: {weather_parameter}"
        )
        model_hour = model_run_for_hour(run_hour)
        adjusted_forecast_hour = adjust_forecast_hour(run_hour, forecast_hour)
        variable = RDPS_VARIABLE_NAMES[weather_parameter]
        date_str = forecast_start_date.date().isoformat().replace("-", "")
        return f"{date_str}T{model_hour:02d}Z_MSC_RDPS_{variable}_RLatLon0.09_PT{adjusted_forecast_hour:03d}H.grib2"

    def _compose_rdps_filename_hffmc(
        self, model_run_start: datetime, offset_hour: int, weather_parameter: str
    ) -> str:
        """Compose RDPS hffmc S3 filename in new MSC format."""
        assert weather_parameter in RDPS_VARIABLE_NAMES, (
            f"Unknown weather parameter: {weather_parameter}"
        )
        variable = RDPS_VARIABLE_NAMES[weather_parameter]
        date_str = model_run_start.date().isoformat().replace("-", "")
        return f"{date_str}T{model_run_start.hour:02d}Z_MSC_RDPS_{variable}_RLatLon0.09_PT{offset_hour:03d}H.grib2"

    def _compose_computed_rdps_filename(self, accumulation_end_datetime: datetime) -> str:
        """Compose a computed RDPS precip filename."""
        key_params = self.weather_key_parameters["precip"]
        file_ext = ".tif"
        return (
            f"{self.COMPUTED}{self.DELIMITER}{self.REG}{self.DELIMITER}{key_params.variable}{self.DELIMITER}{key_params.level_type}{self.DELIMITER}{key_params.level}{self.DELIMITER}{ProjectionEnum.REGIONAL_PS.value}{self.DELIMITER}"
            f"{accumulation_end_datetime.strftime(f'%Y%m%d{self.DELIMITER}%Hz')}{file_ext}"
        )
