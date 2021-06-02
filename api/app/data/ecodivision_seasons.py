""" Defines singleton class that keeps ecodivisions in memory for reuse """
import os
import json
import logging
import geopandas
from shapely.geometry import Point


class Singleton:
    """ Non thread-safe singleton decorator """

    def __init__(self, decorated):
        self._decorated = decorated

    def instance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        try:
            return self._instance
        except AttributeError:
            # pylint: disable=attribute-defined-outside-init
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)


dirname = os.path.dirname(__file__)
core_season_file_path = os.path.join(
    dirname, 'ecodivisions_core_seasons.json')
ecodiv_shape_file_path = os.path.join(
    dirname, 'ERC_ECODIV_polygon/ERC_ECODIV_polygon.shp')

logger = logging.getLogger(__name__)


@Singleton
class EcodivisionSeasons:
    """ Singleton that loads ecodivision data once and keeps it in memory for reuse.
        No mutators, data loaded is immutable."""

    def __init__(self):
        with open(core_season_file_path) as file_handle:
            core_seasons = json.load(file_handle)
        self.core_seasons = core_seasons
        self.ecodivisions = geopandas.read_file(ecodiv_shape_file_path)

    def get_core_seasons(self):
        """Returns core seasons"""
        return self.core_seasons

    def get_ecodivision_name(self, latitude: str, longitude: str):
        """ Returns the ecodivision name for a given lat/long coordinate """
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
        logger.error('Ecodivision not found for station at lat %f long %f', latitude, longitude)
        return "DEFAULT"
