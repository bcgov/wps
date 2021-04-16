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


class WeatherVariables(BaseModel):
    """ Weather variables """
    temperature: float = None
    relative_humidity: float = None


class DetailedWeatherStationProperties(WeatherStationProperties):
    """ Detailed, non-geometrical weather station properties """
    observations: WeatherVariables = None
    forecasts: WeatherVariables = None


class WeatherStationGeometry(BaseModel):
    """ Geometrical coordinates of a weather station """
    type: str = "Point"
    coordinates: List[float]


class GeoJsonWeatherStation(BaseModel):
    """ GeoJson formatted weather station """
    type: str = "Feature"
    properties: WeatherStationProperties
    geometry: WeatherStationGeometry


class GeoJsonDetailedWeatherStation(BaseModel):
    """ GeoJson formatted weather station with details """
    type: str = "Feature"
    properties: DetailedWeatherStationProperties
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
    """ List of fire weather stations in geojson format. """
    type: str = "FeatureCollection"
    features: List[GeoJsonWeatherStation]


class DetailedWeatherStationsResponse(BaseModel):
    """ List of fire weather stations, with details, in geojson format. """
    type: str = "FeatureCollection"
    features: List[GeoJsonDetailedWeatherStation]


class StationCodeList(BaseModel):
    """ List of station codes. """
    stations: List[int]
