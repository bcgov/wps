"""Schemas for station climatology."""

from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class ClimatologyVariable(str, Enum):
    """The daily values climatology is available for: weather, and the FWI System indices WF1
    calculated from it."""

    TEMPERATURE = "temperature"
    RELATIVE_HUMIDITY = "relative_humidity"
    WIND_SPEED = "wind_speed"
    PRECIPITATION = "precipitation"
    FFMC = "ffmc"
    DMC = "dmc"
    DC = "dc"
    ISI = "isi"
    BUI = "bui"
    FWI = "fwi"


class ClimatologyMethod(str, Enum):
    """How the stations asked for are combined. With one station they are all the same."""

    # Each day's value is the mean of the stations that reported it, and the distribution is of
    # those means across years.
    AVERAGE = "average"
    # The distribution is of every station's value on that day across years. The selected year
    # is the mean of the stations, as for AVERAGE.
    POOLED = "pooled"
    # A climatology for each station on its own.
    EACH = "each"


class ClimatologyDay(BaseModel):
    """How a variable has been distributed on one day of the year, over the reference years."""

    month: int
    day: int
    # How many values the distribution is drawn from: years, or station years when pooled.
    count: int
    # How many stations contributed to it.
    station_count: int
    minimum: float
    p25: float
    median: float
    p75: float
    p90: float
    maximum: float


class ClimatologyObservation(BaseModel):
    """The daily value on a date: one station's, or the mean of the stations that reported."""

    date: date
    value: float
    station_count: int


class ClimatologySeries(BaseModel):
    """A daily climatology for some stations, and their values in the selected year."""

    station_codes: List[int]
    # The first and last of the years the distribution is drawn from, which leave out the
    # selected year. None with no history.
    first_reference_year: Optional[int] = None
    last_reference_year: Optional[int] = None
    days: List[ClimatologyDay]
    observations: List[ClimatologyObservation]


class DailyClimatologyResponse(BaseModel):
    """The daily climatology of the stations asked for: one series when they are combined, or
    one per station."""

    variable: ClimatologyVariable
    year: int
    method: ClimatologyMethod
    series: List[ClimatologySeries]


class ClimatologyStation(BaseModel):
    code: int
    name: str
    # The fire zone, such as K2, if WF1 has one for the station.
    zone: Optional[str] = None


class ClimatologyFireCentre(BaseModel):
    """A fire centre and its stations, as a group to choose stations from."""

    id: int
    name: str
    stations: List[ClimatologyStation]


class ClimatologyFireCentresResponse(BaseModel):
    fire_centres: List[ClimatologyFireCentre]
