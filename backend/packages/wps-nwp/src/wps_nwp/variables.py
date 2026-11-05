from dataclasses import dataclass
from enum import StrEnum


class Variable(StrEnum):
    """
    Surface variables with the same meaning across every model that provides them.

    Each has one unit whichever model it comes from; see the units property.
    """

    T2M = "t2m"  # air temperature 2 m above ground
    D2M = "d2m"  # dewpoint 2 m above ground
    RH2M = "rh2m"  # relative humidity 2 m above ground
    # Wind components are relative to the model grid, not to true north, on rotated and
    # projected grids (RDPS, HRDPS, NAM). Use WIND_SPEED_10M / WIND_DIR_10M there.
    U10 = "u10"
    V10 = "v10"
    WIND_SPEED_10M = "wind_speed_10m"
    WIND_DIR_10M = "wind_dir_10m"  # direction the wind blows from
    PRECIP = "precip"  # precipitation accumulated since the start of the run

    @property
    def units(self) -> str:
        """The units this variable's values are returned in, whichever model they are from."""
        return _UNITS[self]


_UNITS = {
    Variable.T2M: "K",
    Variable.D2M: "K",
    Variable.RH2M: "%",
    Variable.U10: "m s-1",
    Variable.V10: "m s-1",
    Variable.WIND_SPEED_10M: "m s-1",
    Variable.WIND_DIR_10M: "degrees true",
    Variable.PRECIP: "mm",
}


@dataclass(frozen=True)
class Native:
    """
    A field named in the model's own vocabulary, for anything Variable does not cover.

    What the selector means depends on the model family:

    - ECMWF open data: "param" or "param:levelist", e.g. Native("msl"), Native("t:850")
    - NOAA: a regex searched against the wgrib2 .idx line, e.g. Native(":TMP:850 mb:")
    - ECCC: the variable and level part of the file name, e.g. Native("AirTemp_IsbL-0850")
    """

    selector: str

    def __str__(self) -> str:
        """The selector, so that messages name the variable as the caller wrote it."""
        return self.selector
