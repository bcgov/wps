""" This module contains pydandict schemas relating to weather stations for the API.
"""
from typing import List, Optional
from pydantic import BaseModel


class FireZone(BaseModel):
    id: int
    display_label: str
    fire_centre: str


class StationFireCentre(BaseModel):
    """ The fire centre associated with a station """
    id: int
    display_label: str


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
    ecodivision_name: Optional[str] = None
    core_season: Optional[Season] = None


class WeatherVariables(BaseModel):
    """ Weather variables """
    temperature: Optional[float] = None
    relative_humidity: Optional[float] = None


class DetailedWeatherStationProperties(WeatherStationProperties):
    """ Detailed, non-geometrical weather station properties """
    observations: Optional[WeatherVariables] = None
    forecasts: Optional[WeatherVariables] = None


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
    zone_code: Optional[str] = None
    code: int
    name: str
    lat: float
    long: float
    ecodivision_name: Optional[str] = None
    core_season: Optional[Season] = None
    elevation: Optional[int] = None
    wfwx_station_uuid: Optional[str] = None


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


class WeatherStationGroupMember(BaseModel):
    """ Description of a station in a group"""
    id: str
    display_label: str
    fire_centre: StationFireCentre
    fire_zone: Optional[FireZone] = None
    station_code: int
    station_status: str


class WeatherStationGroupMembersResponse(BaseModel):
    """ Response to a request for the stations in a group """
    stations: List[WeatherStationGroupMember]


class WeatherStationGroup(BaseModel):
    """ A weather station group from WF1"""
    display_label: str
    group_description: Optional[str] = None
    group_owner_user_guid: str
    group_owner_user_id: str
    id: str


class WeatherStationGroupsResponse(BaseModel):
    """ Response to a request for all WFWX groups"""
    groups: List[WeatherStationGroup]


class WeatherStationGroupsMemberRequest(BaseModel):
    """ Request for all station members of all groups by group ids"""
    group_ids: List[str]
