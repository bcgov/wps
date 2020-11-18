""" Contains code common to app.model.fetch """
import logging
from typing import List
from shapely.geometry import Point, Polygon
from app.schemas.stations import WeatherStation


logger = logging.getLogger(__name__)


def extract_stations_in_polygon(stations: List[WeatherStation], polygon: Polygon) -> List[List]:
    """ Given a list of stations, return all the stations within the specified polygon. """
    return [station for station in stations if Point(station.long, station.lat).within(polygon)]
