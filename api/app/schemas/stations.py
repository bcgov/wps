""" This module contains pydandict schemas relating to weather stations for the API.
"""
from typing import List
from pydantic import BaseModel


class Season(BaseModel):
    """ A fire season consists of a start date (month and day) and an end date (month and day). """
    start_month: int
    start_day: int
    end_month: int
    end_day: int


class WeatherStationProperties(BaseModel):
    """ Non-geometrical weather station properties """
    code: int
    name: str
    ecodivision_name: str = None
    core_season: Season = None


class WeatherStationGeometry(BaseModel):
    """ Geometrical coordinates of a weather station """
    type: str
    coordinates: List[float]


class GeoJsonWeatherStation(BaseModel):
    """ GeoJson formatted weather station """
    type: str
    properties: WeatherStationProperties
    geometry: WeatherStationGeometry


class WeatherStation(BaseModel):
    """ A fire weather station has a code, name and geographical coordinate. """
    code: int
    name: str
    lat: float
    long: float
    ecodivision_name: str = None
    core_season: Season = None


class WeatherStationsResponse(BaseModel):
    """ List of fire weather stations is geojson format. """
    type: str
    features: List[GeoJsonWeatherStation]


class StationCodeList(BaseModel):
    """ List of station codes. """
    stations: List[int]
