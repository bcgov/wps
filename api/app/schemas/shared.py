""" This module contains shared pydantic schemas.
"""

from typing import List
from pydantic import BaseModel


class WeatherDataRequest(BaseModel):
    """ A request for weather data for a given set of stations with a time of interest. """
    stations: List[int]
    time_of_interest: str = None
