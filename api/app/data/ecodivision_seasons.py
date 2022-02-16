""" Defines singleton class that keeps ecodivisions in memory for reuse """
import os
import json
import logging
import geopandas
from typing import Dict
from shapely.geometry import Point
from app.utils.redis import create_redis


dirname = os.path.dirname(__file__)
core_season_file_path = os.path.join(
    dirname, 'ecodivisions_core_seasons.json')
ecodiv_shape_file_path = os.path.join(
    dirname, 'ERC_ECODIV_polygon/ERC_ECODIV_polygon.shp')

logger = logging.getLogger(__name__)


class EcodivisionSeasons:
    """ Singleton that loads ecodivision data once and keeps it in memory for reuse.
        No mutators, data loaded is immutable."""

    def __init__(self, key: str, use_cache: bool = True):
        with open(core_season_file_path, encoding="utf-8") as file_handle:
            core_seasons = json.load(file_handle)
        self.core_seasons = core_seasons
        self.ecodivisions = geopandas.read_file(ecodiv_shape_file_path)
        self.name_lookup: Dict[str, str] = None
        if use_cache:
            self.redis_key = f'ecodivision_names:{key}'
            self.cache = create_redis()
            self.name_lookup = self.cache.get(self.redis_key)
            if self.name_lookup is None:
                self.name_lookup = {}
                self.update_cache = True
            else:
                self.update_cache = False
                self.name_lookup = json.loads(self.name_lookup)
        else:
            self.update_cache = False

    def cache_ecodivision_names(self):
        """ Caches ecodivision names in redis """
        if self.update_cache:
            # cache the result for a day
            self.cache.set(self.redis_key, json.dumps(self.name_lookup), ex=86400)

    def get_core_seasons(self):
        """Returns core seasons"""
        return self.core_seasons

    def _calculate_ecodivision_name(self, station_code: str, latitude: float, longitude: float) -> str:
        if latitude >= 60:
            return 'SUB-ARCTIC HIGHLANDS'
        station_coord = Point(float(longitude), float(latitude))
        for _, ecodivision_row in self.ecodivisions.iterrows():
            geom = ecodivision_row['geometry']
            if station_coord.within(geom):
                return ecodivision_row['CDVSNNM']

        # If we've reached here, the ecodivision for the station has not been found.
        logger.error('Ecodivision not found for station code %s at lat %f long %f',
                     station_code, latitude, longitude)
        return "DEFAULT"

    def get_ecodivision_name(self, station_code: str, latitude: float, longitude: float):
        """ Returns the ecodivision name for a given lat/long coordinate """
        # if station's latitude >= 60 (approx.), it's in the Yukon, so it won't be captured
        # in the shapefile, but it's considered to be part of the SUB-ARCTIC HIGHLANDS ecodivision.
        key = f'{station_code}:{latitude}:{longitude}'
        value = self.name_lookup.get(key, None)
        if value is None:
            value = self._calculate_ecodivision_name(station_code, latitude, longitude)
            self.name_lookup[key] = value
        return value
