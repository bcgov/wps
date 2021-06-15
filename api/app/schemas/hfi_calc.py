""" This module contains pydandict schemas relating to the HFI Calculator for the API.
"""
from typing import List
from pydantic import BaseModel


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
