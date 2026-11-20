"""The values the model jobs pass between steps, in memory. A run's values come from `staging`,
and its station predictions go to `runs` and `by_time`; nothing here is a database row."""

import logging
from dataclasses import asdict, dataclass
from datetime import datetime

import numpy as np

logger = logging.getLogger(__name__)


def _plain(value):
    return value.item() if isinstance(value, np.float64) else value


@dataclass
class ModelValues:
    """A model's values at a station and time, as extracted from the model's grid."""

    station_code: int | None = None
    prediction_timestamp: datetime | None = None
    # Temperature 2m above model layer.
    tmp_tgl_2: float | None = None
    # Relative humidity 2m above model layer.
    rh_tgl_2: float | None = None
    # Accumulated precipitation (units kg.m^-2)
    apcp_sfc_0: float | None = None
    # Wind direction 10m above ground.
    wdir_tgl_10: float | None = None
    # Wind speed 10m above ground.
    wind_tgl_10: float | None = None
    # Set on an interpolated noon value only.
    delta_precip: float | None = None

    @classmethod
    def from_staging(cls, station_code: int, values: dict) -> "ModelValues":
        """Build from one of StagingTable.station_values' dicts."""
        return cls(
            station_code=station_code,
            prediction_timestamp=values["prediction_timestamp"],
            tmp_tgl_2=values["tmp_tgl_2"],
            rh_tgl_2=values["rh_tgl_2"],
            apcp_sfc_0=values["apcp_sfc_0"],
            wdir_tgl_10=values["wdir_tgl_10"],
            wind_tgl_10=values["wind_tgl_10"],
        )

    def _get_field_value(self, field_name: str, field_value) -> float | None:
        value = _plain(field_value)
        if value is None:
            logger.warning(
                "%s is None for station %s at %s",
                field_name,
                self.station_code,
                self.prediction_timestamp,
            )
        return value

    def get_temp(self) -> float | None:
        return self._get_field_value("tmp_tgl_2", self.tmp_tgl_2)

    def get_rh(self) -> float | None:
        return self._get_field_value("rh_tgl_2", self.rh_tgl_2)

    def get_precip(self) -> float:
        precip = self._get_field_value("apcp_sfc_0", self.apcp_sfc_0)
        return precip if precip is not None else 0.0

    def get_wind_speed(self) -> float | None:
        return self._get_field_value("wind_tgl_10", self.wind_tgl_10)

    def get_wind_direction(self) -> float | None:
        return self._get_field_value("wdir_tgl_10", self.wdir_tgl_10)


@dataclass
class StationPrediction:
    """A station prediction of a model run, with its bias adjustments: one row of `runs`."""

    station_code: int | None = None
    prediction_timestamp: datetime | None = None
    tmp_tgl_2: float | None = None
    rh_tgl_2: float | None = None
    apcp_sfc_0: float | None = None
    wdir_tgl_10: float | None = None
    wind_tgl_10: float | None = None
    bias_adjusted_temperature: float | None = None
    bias_adjusted_rh: float | None = None
    bias_adjusted_wdir: float | None = None
    bias_adjusted_wind_speed: float | None = None
    delta_precip: float | None = None
    precip_24h: float | None = None
    bias_adjusted_precip_24h: float | None = None
    # Whether the job interpolated the row between two of the model's own times.
    is_interpolated: bool = False

    def as_row(self) -> dict:
        """The row for RunsTable.append_run and ByTimeTable.merge_run."""
        return {key: _plain(value) for key, value in asdict(self).items()}
