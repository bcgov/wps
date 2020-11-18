""" This module contains pydandict schemas relating to the percentile calculator for the API.
"""
from typing import List, Dict
from pydantic import BaseModel
from app.schemas.stations import WeatherStation


class YearRange(BaseModel):
    """ A request for data spans a range of years. """
    start: int
    end: int


class PercentileRequest(BaseModel):
    """ A request for some quantile for a given set of stations over a specified year range. """
    stations: List[int]
    percentile: int
    year_range: YearRange


class StationSummary(BaseModel):
    """ The summary of daily weather data for a given station. """
    ffmc: float = None
    isi: float = None
    bui: float = None
    years: List[int]
    station: WeatherStation


class MeanValues(BaseModel):
    """ The mean percentile values for set of stations. """
    ffmc: float = None
    isi: float = None
    bui: float = None


class CalculatedResponse(BaseModel):
    """ The combined response for a set of stations. """
    stations: Dict[int, StationSummary] = {}
    mean_values: MeanValues = None
    year_range: YearRange
    percentile: int
