"""This module contains pydandict schemas relating to observations (a.k.a. hourlies) for the API."""

from typing import List

from pydantic import BaseModel
from wps_wf1.models import WeatherStationHourlyReadings


class WeatherStationHourlyReadingsResponse(BaseModel):
    """Response containing a number of hourly readings."""

    hourlies: List[WeatherStationHourlyReadings]
