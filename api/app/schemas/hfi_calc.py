""" This module contains pydandict schemas the HFI Calculator.
"""
from typing import List, Union
from pydantic import BaseModel


class StationDaily(BaseModel):
    """ Station Daily metrics for HFI daily table """
    code: Union[int, None] = None
    status: Union[str, None] = None
    temperature: Union[float, None] = None
    relative_humidity: Union[float, None] = None
    wind_speed: Union[float, None] = None
    wind_direction: Union[float, None] = None
    grass_cure_percentage: Union[float, None] = None
    precipitation: Union[float, None] = None
    ffmc: Union[float, None] = None
    dmc: Union[float, None] = None
    dc: Union[float, None] = None
    isi: Union[float, None] = None
    bui: Union[float, None] = None
    fwi: Union[float, None] = None
    danger_cl: Union[int, None] = None
    observation_valid: Union[bool, None] = None
    observation_valid_comment: Union[str, None] = None


class StationDailyResponse(BaseModel):
    """ Response that includes list of station daily data."""
    dailies: List[StationDaily]


class FuelType(BaseModel):
    """ Fuel type assigned to a station for HFI calculation purposes. """
    abbrev: str
    description: str


class WeatherStationProperties(BaseModel):
    """ HFI-relevant weather station properties """
    name: str
    elevation: int
    fuel_type: FuelType
    wfwx_station_uuid: str


class WeatherStation(BaseModel):
    """ A fire weather station has a code, planning area, and other properties specific to the station. """
    code: int
    station_props: WeatherStationProperties


class PlanningArea(BaseModel):
    """ A planning area (a.k.a. zone) is a small group of stations selected to represent a particular
    zone within a fire centre. """
    name: str
    stations: List[WeatherStation]


class FireCentre(BaseModel):
    """ The highest-level organizational unit for wildfire planning. Each fire centre
    has 1 or more planning areas within it. """
    name: str
    planning_areas: List[PlanningArea]


class HFIWeatherStationsResponse(BaseModel):
    """ A list of WeatherStations, where each WeatherStation has nested within it all relevant information
    specific to BCWS planning operations. """
    fire_centres: List[FireCentre]
