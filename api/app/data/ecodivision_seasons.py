""" Defines singleton class that keeps ecodivisions in memory for reuse """
import os
import json
from typing import Dict
import logging
import geopandas
from shapely.geometry import Point
from app.utils.redis import create_redis


dirname = os.path.dirname(__file__)
core_season_file_path = os.path.join(
    dirname, 'ecodivisions_core_seasons.json')
ecodiv_shape_file_path = os.path.join(
    dirname, 'ERC_ECODIV_polygon/ERC_ECODIV_polygon.shp')

logger = logging.getLogger(__name__)


class EcodivisionSeasons:
    """ Calculate ecodivisions, or do in memory lookup.
    When used within a context manager, the in memory lookup uses redis as cache.

    Caching one ecodivision in redis at a time isn't really a time save, it's faster to calculate a single
    ecodivision, than look it up. Where it is a big time save, is caching the ecodivisions for a set of
    stations.
    """

    def __init__(self, cache_key: str):
        """ The cache key would typically be a list of stations.
        """
        with open(core_season_file_path, encoding="utf-8") as file_handle:
            core_seasons = json.load(file_handle)
        self.core_seasons = core_seasons
        self.ecodivisions = geopandas.read_file(ecodiv_shape_file_path)
        self.name_lookup: Dict[str, str] = {}
        self.cache_key = cache_key
        self.cache = None
        self.update_cache_on_exit = False

    def __enter__(self):
        if self.cache_key:
            self.cache_key = f'ecodivision_names:{self.cache_key}'
            self.cache = create_redis()
            try:
                self.name_lookup = self.cache.get(self.cache_key)
                if self.name_lookup is None:
                    # cache failed - so just use an empty dict.
                    self.name_lookup = {}
                    # flag that we want to save this when we're done
                    self.update_cache_on_exit = True
                else:
                    logger.info('redis cache hit %s', self.cache_key)
                    self.name_lookup = json.loads(self.name_lookup)
            except Exception as error:  # pylint: disable=broad-except
                # set the look to an empty dictionary.
                self.name_lookup = {}
                # set the cache object to None, so that we don't try to use
                # the cache again.
                self.cache = None
                logger.error(error)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Caches ecodivision names in redis """
        if self.cache and self.cache_key and self.update_cache_on_exit:
            # cache the result for a day
            try:
                self.cache.set(self.cache_key, json.dumps(self.name_lookup), ex=86400)
            except Exception as error:  # pylint: disable=broad-except
                # redis cache failing isn't a critical failure. we log it and keep
                # going.
                logger.error(error)

    def get_core_seasons(self):
        """Returns core seasons"""
        return self.core_seasons

    def _calculate_ecodivision_name(self, station_code: str, latitude: float, longitude: float) -> str:
        """ Calculate and return the ecodivision name for a given lat/long coordinate """
        # if station's latitude >= 60 (approx.), it's in the Yukon, so it won't be captured
        # in the shapefile, but it's considered to be part of the SUB-ARCTIC HIGHLANDS ecodivision.
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
        # 1st we look to see if we have this one cached:
        key = f'{station_code}:{latitude}:{longitude}'
        value = self.name_lookup.get(key, None)
        if value is None:
            # Flag that we want to update the cache when we're done.
            self.update_cache_on_exit = True
            # We don't have it cached, so calculate it and cache it:
            value = self._calculate_ecodivision_name(station_code, latitude, longitude)
            self.name_lookup[key] = value
        return value
