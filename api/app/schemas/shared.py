""" This module contains shared pydantic schemas.
"""

from typing import List
from datetime import datetime
from pydantic import BaseModel
import app.utils.time as time_utils


class WeatherDataRequest(BaseModel):
    """ A request for weather data for a given set of stations with a time of interest. """
    stations: List[int]
    time_of_interest: datetime = time_utils.get_utc_now()
