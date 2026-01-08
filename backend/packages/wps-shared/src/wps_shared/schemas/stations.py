"""This module contains pydandict schemas relating to weather stations for the API."""

from typing import List, Optional

from pydantic import BaseModel
from wps_wf1.models import (
    GeoJsonDetailedWeatherStation,
    WeatherStationGeometry,
    WeatherStationGroup,
    WeatherStationGroupMember,
    WeatherStationProperties,
)


class GeoJsonWeatherStation(BaseModel):
    """GeoJson formatted weather station"""

    type: str = "Feature"
    properties: WeatherStationProperties
    geometry: WeatherStationGeometry


class WeatherStationsResponse(BaseModel):
    """List of fire weather stations in geojson format."""

    type: str = "FeatureCollection"
    features: List[GeoJsonWeatherStation]


class DetailedWeatherStationsResponse(BaseModel):
    """List of fire weather stations, with details, in geojson format."""

    type: str = "FeatureCollection"
    features: List[GeoJsonDetailedWeatherStation]


class StationCodeList(BaseModel):
    """List of station codes."""

    stations: List[int]


class WeatherStationGroupMembersResponse(BaseModel):
    """Response to a request for the stations in a group"""

    stations: List[WeatherStationGroupMember]


class WeatherStationGroupsResponse(BaseModel):
    """Response to a request for all WFWX groups"""

    groups: List[WeatherStationGroup]


class WeatherStationGroupsMemberRequest(BaseModel):
    """Request for all station members of all groups by group ids"""

    group_ids: List[str]
