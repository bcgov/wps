from dataclasses import dataclass
import logging
from typing import List

import numpy as np
from numpy.typing import NDArray
from wps_shared.schemas.sfms import SFMSDailyActual

logger = logging.getLogger(__name__)

# Environmental lapse rate: 6.5°C per 1000m elevation (average observed rate)
# This matches the CWFIS implementation.
LAPSE_RATE = 0.0065

# Dew point lapse rate: 2.0°C per 1000m.
DEW_POINT_LAPSE_RATE = 0.002

_VALID_SFMS_ATTRIBUTES = frozenset(SFMSDailyActual.model_fields.keys())


@dataclass(frozen=True)
class ScalarField:
    lats: NDArray[np.float32]
    lons: NDArray[np.float32]
    values: NDArray[np.float32]


@dataclass(frozen=True)
class WindVectorField:
    lats: NDArray[np.float32]
    lons: NDArray[np.float32]
    u: NDArray[np.float32]
    v: NDArray[np.float32]


def compute_sea_level_values(
    values: NDArray[np.float32], elevs: NDArray[np.float32], lapse_rate: float
) -> NDArray[np.float32]:
    """Vectorized: V_sea = V_station + elevation * lapse_rate"""
    values = np.asarray(values, dtype=np.float32)
    elevs = np.asarray(elevs, dtype=np.float32)
    return values + elevs * np.float32(lapse_rate)


def compute_adjusted_values(
    sea: NDArray[np.float32], elev: NDArray[np.float32], lapse_rate: float
) -> NDArray[np.float32]:
    """Vectorized: V(z) = V_sea - z * lapse_rate"""
    sea = np.asarray(sea, dtype=np.float32)
    elev = np.asarray(elev, dtype=np.float32)
    return sea - elev * np.float32(lapse_rate)


def compute_rh(temp: NDArray[np.float32], dewpoint: NDArray[np.float32]) -> NDArray[np.float32]:
    """
    Compute relative humidity from temperature and dew point using the Arden Buck equation.

    Buck (1981): e_s(T) = 6.1121 * exp((18.678 - T/234.5) * (T / (257.14 + T)))
    RH = 100 * e_s(Td) / e_s(T)

    :param temp: Temperature array in Celsius
    :param dewpoint: Dew point temperature array in Celsius
    :return: Relative humidity as percentage (0-100), clamped
    """
    e_td = 6.1121 * np.exp((18.678 - dewpoint / 234.5) * (dewpoint / (257.14 + dewpoint)))
    e_t = 6.1121 * np.exp((18.678 - temp / 234.5) * (temp / (257.14 + temp)))
    rh = 100.0 * e_td / e_t
    return np.clip(rh, 0.0, 100.0).astype(np.float32)


def build_attribute_field(actuals: List[SFMSDailyActual], attribute: str) -> ScalarField:
    if attribute not in _VALID_SFMS_ATTRIBUTES:
        raise ValueError(
            f"Unknown attribute {attribute!r} on SFMSDailyActual. Valid attributes: {sorted(_VALID_SFMS_ATTRIBUTES)}"
        )

    valid = [s for s in actuals if getattr(s, attribute) is not None]
    return ScalarField(
        lats=np.array([s.lat for s in valid], dtype=np.float32),
        lons=np.array([s.lon for s in valid], dtype=np.float32),
        values=np.array([getattr(s, attribute) for s in valid], dtype=np.float32),
    )


def build_temperature_field(actuals: List[SFMSDailyActual]) -> ScalarField:
    return _build_lapse_rate_field(actuals, "temperature", LAPSE_RATE, "temperature")


def build_dewpoint_field(actuals: List[SFMSDailyActual]) -> ScalarField:
    return _build_lapse_rate_field(actuals, "dewpoint", DEW_POINT_LAPSE_RATE, "dew point")


def build_precipitation_field(actuals: List[SFMSDailyActual]) -> ScalarField:
    return build_attribute_field(actuals, "precipitation")


def build_wind_speed_field(actuals: List[SFMSDailyActual]) -> ScalarField:
    return build_attribute_field(actuals, "wind_speed")


def build_ffmc_field(actuals: List[SFMSDailyActual]) -> ScalarField:
    return build_attribute_field(actuals, "ffmc")


def build_dmc_field(actuals: List[SFMSDailyActual]) -> ScalarField:
    return build_attribute_field(actuals, "dmc")


def build_dc_field(actuals: List[SFMSDailyActual]) -> ScalarField:
    return build_attribute_field(actuals, "dc")


def build_wind_vector_field(actuals: List[SFMSDailyActual]) -> WindVectorField:
    valid = [s for s in actuals if s.wind_speed is not None and s.wind_direction is not None]
    if not valid:
        empty = np.array([], dtype=np.float32)
        return WindVectorField(empty, empty, empty, empty)

    lats = np.array([s.lat for s in valid], dtype=np.float32)
    lons = np.array([s.lon for s in valid], dtype=np.float32)
    speed = np.array([s.wind_speed for s in valid], dtype=np.float32)
    direction = np.array([s.wind_direction for s in valid], dtype=np.float32)

    direction_radians = np.radians(direction.astype(np.float32))
    u = (-speed * np.sin(direction_radians)).astype(np.float32)
    v = (-speed * np.cos(direction_radians)).astype(np.float32)
    return WindVectorField(lats=lats, lons=lons, u=u, v=v)


def _build_lapse_rate_field(
    actuals: List[SFMSDailyActual], attribute: str, lapse_rate: float, label: str
) -> ScalarField:
    lats = np.array([a.lat for a in actuals], dtype=np.float32)
    lons = np.array([a.lon for a in actuals], dtype=np.float32)
    elevs = np.array(
        [a.elevation if a.elevation is not None else np.nan for a in actuals], dtype=np.float32
    )
    values = np.array(
        [getattr(a, attribute) if getattr(a, attribute) is not None else np.nan for a in actuals],
        dtype=np.float32,
    )
    valid = np.isfinite(elevs) & np.isfinite(values)

    if not np.any(valid):
        logger.warning(
            "No valid %s stations (missing elevation or value) — interpolation will produce no output",
            label,
        )

    return ScalarField(
        lats=lats[valid],
        lons=lons[valid],
        values=compute_sea_level_values(values[valid], elevs[valid], lapse_rate),
    )
