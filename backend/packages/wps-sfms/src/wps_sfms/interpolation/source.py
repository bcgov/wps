import logging
from typing import List, Optional, Protocol, Tuple, runtime_checkable
import numpy as np

from numpy.typing import NDArray
from wps_shared.schemas.sfms import SFMSDailyActual
from wps_sfms.interpolation.fields import (
    DEW_POINT_LAPSE_RATE,
    LAPSE_RATE,
    build_attribute_field,
    build_wind_vector_field,
    compute_adjusted_values,
    compute_rh,
    compute_sea_level_values,
)

logger = logging.getLogger(__name__)


@runtime_checkable
class StationInterpolationSource(Protocol):
    def get_interpolation_data(
        self,
    ) -> Tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]]: ...


class LapseRateAdjustedSource:
    """
    Compatibility wrapper for station sources requiring lapse-rate adjustment.

    This preserves the older source API for tools/tests while delegating the
    underlying interpolation math to the field-builder helpers.
    """

    _attribute: str

    def __init__(self, sfms_actuals: List[SFMSDailyActual]):
        self._sfms_actuals = sfms_actuals
        self._lats: Optional[NDArray[np.float32]] = None
        self._lons: Optional[NDArray[np.float32]] = None
        self._elevs: Optional[NDArray[np.float32]] = None
        self._values: Optional[NDArray[np.float32]] = None
        self._valid_mask: Optional[NDArray[np.float32]] = None

    @staticmethod
    def compute_sea_level_values(
        values: NDArray[np.float32], elevs: NDArray[np.float32], lapse_rate: float
    ) -> NDArray[np.float32]:
        """Vectorized: V_sea = V_station + elevation * lapse_rate."""
        return compute_sea_level_values(values, elevs, lapse_rate)

    @staticmethod
    def compute_adjusted_values(
        sea: NDArray[np.float32], elev: NDArray[np.float32], lapse_rate: float
    ) -> NDArray[np.float32]:
        """Vectorized: V(z) = V_sea - z * lapse_rate."""
        return compute_adjusted_values(sea, elev, lapse_rate)

    def get_station_count(self) -> int:
        return len(self._sfms_actuals)

    def get_station_arrays(
        self, only_valid: bool = True
    ) -> Tuple[
        NDArray[np.float32],
        NDArray[np.float32],
        NDArray[np.float32],
        NDArray[np.float32],
    ]:
        """
        Returns (lats, lons, elevs, values) as NumPy arrays (float32).
        If only_valid=True, filters out stations missing elevation or value.
        """
        self._ensure_arrays()
        if only_valid:
            v = self._valid_mask
            return self._lats[v], self._lons[v], self._elevs[v], self._values[v]
        return self._lats, self._lons, self._elevs, self._values

    def get_interpolation_data(
        self, lapse_rate: float = LAPSE_RATE
    ) -> Tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]]:
        """Returns arrays for IDW: (lats, lons, sea_level_values), vectorized."""
        lats, lons, elevs, values = self.get_station_arrays(only_valid=True)
        if lats.size == 0:
            logger.warning(
                "%s has no valid stations (missing elevation or value) — interpolation will produce no output",
                type(self).__name__,
            )
            return lats, lons, values

        sea = self.compute_sea_level_values(values, elevs, lapse_rate)
        return lats, lons, sea

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _ensure_arrays(self) -> None:
        if self._lats is None:
            self._materialize_arrays()

    @staticmethod
    def _optional_to_array(actuals: List[SFMSDailyActual], attr: str) -> NDArray[np.float32]:
        """Extract an optional float attribute from each actual into a float32 array (None → nan)."""
        return np.array(
            [getattr(a, attr) if getattr(a, attr) is not None else np.nan for a in actuals],
            dtype=np.float32,
        )

    def _materialize_arrays(self) -> None:
        """Pulls values from sfms_actuals into float32 NumPy arrays and computes valid mask."""
        actuals = self._sfms_actuals
        self._lats = np.array([a.lat for a in actuals], dtype=np.float32)
        self._lons = np.array([a.lon for a in actuals], dtype=np.float32)
        self._elevs = self._optional_to_array(actuals, "elevation")
        self._values = self._optional_to_array(actuals, self._attribute)
        self._valid_mask = np.isfinite(self._elevs) & np.isfinite(self._values)


class StationTemperatureSource(LapseRateAdjustedSource):
    """Station source for temperature values with lapse-rate elevation adjustment."""

    _attribute = "temperature"


class StationDewPointSource(LapseRateAdjustedSource):
    """
    Station source for dew-point values (computed from temperature + RH)
    with lapse-rate elevation adjustment.
    """

    _attribute = "dewpoint"

    @staticmethod
    def compute_rh(temp: np.ndarray, dewpoint: np.ndarray) -> np.ndarray:
        """
        :param temp: Temperature array in Celsius
        :param dewpoint: Dew point temperature array in Celsius
        :return: Relative humidity as percentage (0-100), clamped
        """
        return compute_rh(
            np.asarray(temp, dtype=np.float32),
            np.asarray(dewpoint, dtype=np.float32),
        )


_VALID_SFMS_ATTRIBUTES = frozenset(SFMSDailyActual.model_fields.keys())


class StationActualSource(StationInterpolationSource):
    """Generic source for interpolating a named attribute from SFMSDailyActual."""

    def __init__(self, attribute: str, sfms_actuals: List[SFMSDailyActual]):
        if attribute not in _VALID_SFMS_ATTRIBUTES:
            raise ValueError(
                f"Unknown attribute {attribute!r} on SFMSDailyActual. Valid attributes: {sorted(_VALID_SFMS_ATTRIBUTES)}"
            )
        self._attribute = attribute
        self._sfms_actuals = sfms_actuals

    def get_interpolation_data(
        self,
    ) -> Tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]]:
        field = build_attribute_field(self._sfms_actuals, self._attribute)
        return field.lats, field.lons, field.values


class StationWindVectorSource:
    """
    Station source for paired wind speed/direction transformed to u/v vectors.

    Unlike `StationInterpolationSource`, wind interpolation needs two value arrays
    (u and v), so this source returns four arrays: `(lats, lons, u, v)`.
    """

    def __init__(self, sfms_actuals: List[SFMSDailyActual]):
        self._sfms_actuals = sfms_actuals

    def get_interpolation_data(
        self,
    ) -> Tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]]:
        field = build_wind_vector_field(self._sfms_actuals)
        return field.lats, field.lons, field.u, field.v


def StationPrecipitationSource(sfms_actuals: List[SFMSDailyActual]) -> StationActualSource:
    return StationActualSource("precipitation", sfms_actuals)


def StationWindSpeedSource(sfms_actuals: List[SFMSDailyActual]) -> StationActualSource:
    return StationActualSource("wind_speed", sfms_actuals)


def StationFFMCSource(sfms_actuals: List[SFMSDailyActual]) -> StationActualSource:
    return StationActualSource("ffmc", sfms_actuals)


def StationDMCSource(sfms_actuals: List[SFMSDailyActual]) -> StationActualSource:
    return StationActualSource("dmc", sfms_actuals)


def StationDCSource(sfms_actuals: List[SFMSDailyActual]) -> StationActualSource:
    return StationActualSource("dc", sfms_actuals)
