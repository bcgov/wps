"""Schemas for station climatology."""

from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class ClimatologyVariable(str, Enum):
    """The daily weather values climatology is available for."""

    TEMPERATURE = "temperature"
    RELATIVE_HUMIDITY = "relative_humidity"
    WIND_SPEED = "wind_speed"
    PRECIPITATION = "precipitation"


class ClimatologyDay(BaseModel):
    """How a variable has been distributed on one day of the year, over the reference years."""

    month: int
    day: int
    # How many of the reference years have a value on this day.
    count: int
    minimum: float
    p25: float
    median: float
    p75: float
    p90: float
    maximum: float


class ClimatologyObservation(BaseModel):
    """A station's daily value on a date."""

    date: date
    value: float


class DailyClimatologyResponse(BaseModel):
    """A station's daily climatology for a variable, and its values in one year to compare."""

    station_code: int
    variable: ClimatologyVariable
    year: int
    # The first and last of the years the distribution is drawn from, which leave out `year`.
    first_reference_year: Optional[int] = None
    last_reference_year: Optional[int] = None
    days: List[ClimatologyDay]
    observations: List[ClimatologyObservation]
