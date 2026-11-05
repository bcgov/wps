"""
Where each model's output lives and how to find a single field inside it.

A model is a URL template, a list of mirrors and a strategy for locating fields. Adding one
is a matter of declaring another instance; see the catalogue at the bottom of this file.
"""

import json
import re
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from wps_nwp.variables import Native, Variable

Getter = Callable[[str], Awaitable[bytes]]


@dataclass(frozen=True)
class Part:
    """One GRIB field and the bytes of a remote file that hold it."""

    variable: Variable | Native
    url: str
    offset: int = 0
    length: int | None = None  # None reads to the end of the file
    subfield: int | None = None  # position within a multi-field GRIB2 message


@dataclass(frozen=True, eq=False)
class Model(ABC):
    name: str
    path: str  # str.format template, relative to a mirror; receives run and step
    variables: Mapping[Variable, str]  # Variable -> selector in the model's own vocabulary
    mirrors: tuple[str, ...]  # tried in order
    cycles: tuple[int, ...] = (0, 6, 12, 18)  # UTC hours at which the model is run

    def selector(self, variable: Variable | Native) -> str:
        if isinstance(variable, Native):
            return variable.selector
        try:
            return self.variables[variable]
        except KeyError:
            known = ", ".join(self.variables)
            raise ValueError(
                f"{self.name} does not provide {variable.value!r}; it has {known}. "
                "Use Native(...) for anything else."
            ) from None

    def url(self, mirror: str, run: datetime, step: int, **extra: str) -> str:
        return f"{mirror}/{self.path.format(run=run, step=step, **extra)}"

    @abstractmethod
    async def locate(
        self,
        get: Getter,
        mirror: str,
        run: datetime,
        step: int,
        variables: Sequence[Variable | Native],
    ) -> list[Part]:
        """
        Work out which bytes hold each variable.

        Raises NotAvailable if the mirror does not have this step. Variables the step exists
        without (precipitation at hour 0, say) are left out of the result.
        """

    @abstractmethod
    def probe(self, mirror: str, run: datetime, step: int) -> str:
        """A small URL that exists once this step has been published."""


@dataclass(frozen=True, eq=False)
class EcmwfOpenData(Model):
    """One GRIB2 file per step, with a JSON-lines .index giving each field's byte range."""

    def probe(self, mirror: str, run: datetime, step: int) -> str:
        return self.url(mirror, run, step).removesuffix(".grib2") + ".index"

    async def locate(self, get, mirror, run, step, variables) -> list[Part]:
        url = self.url(mirror, run, step)
        index = await get(self.probe(mirror, run, step))
        entries = [json.loads(line) for line in index.splitlines() if line.strip()]
        parts = []
        for variable in variables:
            param, _, level = self.selector(variable).partition(":")
            for entry in entries:
                if entry["param"] == param and entry.get("levelist", "") == level:
                    parts.append(Part(variable, url, entry["_offset"], entry["_length"]))
                    break
        return parts


@dataclass(frozen=True, eq=False)
class NoaaIdx(Model):
    """One GRIB2 file per step, with a wgrib2 .idx listing where each message starts."""

    def probe(self, mirror: str, run: datetime, step: int) -> str:
        return self.url(mirror, run, step) + ".idx"

    async def locate(self, get, mirror, run, step, variables) -> list[Part]:
        url = self.url(mirror, run, step)
        entries = parse_idx((await get(self.probe(mirror, run, step))).decode())
        parts = []
        for variable in variables:
            pattern = re.compile(self.selector(variable))
            for line, offset, length, subfield in entries:
                if pattern.search(line):
                    parts.append(Part(variable, url, offset, length, subfield))
                    break
        return parts


def parse_idx(text: str) -> list[tuple[str, int, int | None, int | None]]:
    """
    Parse a wgrib2 index into (line, offset, length, subfield) rows.

    The index only records where messages start, so a length is the gap to the next message
    and the last message has none. Lines numbered "329.1", "329.2" are fields packed into a
    single message: they share an offset and are told apart by subfield.
    """
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        number, offset, _ = line.split(":", 2)
        _, _, sub = number.partition(".")
        rows.append((line, int(offset), int(sub) - 1 if sub else None))
    offsets = sorted({offset for _, offset, _ in rows})
    following = dict(zip(offsets, offsets[1:]))
    return [
        (line, offset, following[offset] - offset if offset in following else None, subfield)
        for line, offset, subfield in rows
    ]


@dataclass(frozen=True, eq=False)
class MscDatamart(Model):
    """One GRIB2 file per variable per step; the path template also receives var."""

    def probe(self, mirror: str, run: datetime, step: int) -> str:
        return self.url(mirror, run, step, var=next(iter(self.variables.values())))

    async def locate(self, get, mirror, run, step, variables) -> list[Part]:
        return [
            Part(variable, self.url(mirror, run, step, var=self.selector(variable)))
            for variable in variables
        ]


_ECMWF_MIRRORS = (
    "https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com",
    "https://storage.googleapis.com/ecmwf-open-data",
)
_ECMWF_VARIABLES = {
    Variable.T2M: "2t",
    Variable.D2M: "2d",
    Variable.U10: "10u",
    Variable.V10: "10v",
    Variable.PRECIP: "tp",
}

IFS = EcmwfOpenData(
    name="ifs",
    path="{run:%Y%m%d}/{run:%H}z/ifs/0p25/oper/{run:%Y%m%d%H}0000-{step}h-oper-fc.grib2",
    variables=_ECMWF_VARIABLES,
    mirrors=_ECMWF_MIRRORS,
)
AIFS = EcmwfOpenData(
    name="aifs",
    path="{run:%Y%m%d}/{run:%H}z/aifs-single/0p25/oper/{run:%Y%m%d%H}0000-{step}h-oper-fc.grib2",
    variables=_ECMWF_VARIABLES,
    mirrors=_ECMWF_MIRRORS,
)

_NOAA_VARIABLES = {
    Variable.T2M: ":TMP:2 m above ground:",
    Variable.D2M: ":DPT:2 m above ground:",
    Variable.RH2M: ":RH:2 m above ground:",
    Variable.U10: ":UGRD:10 m above ground:",
    Variable.V10: ":VGRD:10 m above ground:",
}

GFS = NoaaIdx(
    name="gfs",
    path="gfs.{run:%Y%m%d}/{run:%H}/atmos/gfs.t{run:%H}z.pgrb2.0p25.f{step:03d}",
    # GFS also carries a 3 or 6 hour bucket; the one starting at 0 is the run total.
    variables={**_NOAA_VARIABLES, Variable.PRECIP: r":APCP:surface:0-\d+ (hour|day) acc"},
    mirrors=(
        "https://noaa-gfs-bdp-pds.s3.amazonaws.com",
        "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod",
    ),
)
# NAM precipitation buckets reset during the run, so there is no run total to map PRECIP to.
# Native(":APCP:surface:") returns the bucket.
NAM = NoaaIdx(
    name="nam",
    path="nam.{run:%Y%m%d}/nam.t{run:%H}z.awphys{step:02d}.tm00.grib2",
    variables=_NOAA_VARIABLES,
    mirrors=("https://noaa-nam-pds.s3.amazonaws.com",),
)

# HPFX has ten times the bandwidth of the Datamart but only best-effort uptime.
_MSC_MIRRORS = ("https://hpfx.collab.science.gc.ca", "https://dd.weather.gc.ca")
_MSC_VARIABLES = {
    Variable.T2M: "AirTemp_AGL-2m",
    Variable.D2M: "DewPoint_AGL-2m",
    Variable.RH2M: "RelativeHumidity_AGL-2m",
    Variable.U10: "WindU_AGL-10m",
    Variable.V10: "WindV_AGL-10m",
    Variable.WIND_SPEED_10M: "WindSpeed_AGL-10m",
    Variable.WIND_DIR_10M: "WindDir_AGL-10m",
    Variable.PRECIP: "Precip-Accum_Sfc",
}
_MSC_PATH = (
    "{{run:%Y%m%d}}/WXO-DD/{directory}/{{run:%H}}/{{step:03d}}/"
    "{{run:%Y%m%dT%H}}Z_MSC_{model}_{{var}}_{grid}_PT{{step:03d}}H.grib2"
)

GDPS = MscDatamart(
    name="gdps",
    path=_MSC_PATH.format(directory="model_gdps/15km", model="GDPS", grid="LatLon0.15"),
    variables=_MSC_VARIABLES,
    mirrors=_MSC_MIRRORS,
    cycles=(0, 12),
)
RDPS = MscDatamart(
    name="rdps",
    path=_MSC_PATH.format(directory="model_rdps/10km", model="RDPS", grid="RLatLon0.09"),
    variables=_MSC_VARIABLES,
    mirrors=_MSC_MIRRORS,
)
HRDPS = MscDatamart(
    name="hrdps",
    path=_MSC_PATH.format(
        directory="model_hrdps/continental/2.5km", model="HRDPS", grid="RLatLon0.0225"
    ),
    variables={
        Variable.T2M: "TMP_AGL-2m",
        Variable.D2M: "DPT_AGL-2m",
        Variable.RH2M: "RH_AGL-2m",
        Variable.U10: "UGRD_AGL-10m",
        Variable.V10: "VGRD_AGL-10m",
        Variable.WIND_SPEED_10M: "WIND_AGL-10m",
        Variable.WIND_DIR_10M: "WDIR_AGL-10m",
        Variable.PRECIP: "APCP_Sfc",
    },
    mirrors=_MSC_MIRRORS,
)

MODELS: dict[str, Model] = {model.name: model for model in (IFS, AIFS, GFS, NAM, GDPS, RDPS, HRDPS)}
