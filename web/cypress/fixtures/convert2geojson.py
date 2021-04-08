import os
import json
from typing import List


class WeatherStationProperties:
    code: int
    name: str
    ecodivision_name: str
    core_season: str

    def __init__(self, code, name, ecodivision_name, core_season):
        self.code = code
        self.name = name
        self.ecodivision_name = ecodivision_name
        self.core_season = core_season


class WeatherStationGeometry:
    type: str
    coordinates: List[float]

    def __init__(self, type, coordinates):
        self.type = type
        self.coordinates = coordinates


class GeoJsonWeatherStation:
    type: str
    properties: WeatherStationProperties
    geometry: WeatherStationGeometry

    def __init__(self, type, properties, geometry):
        self.type = type
        self.properties = properties
        self.geometry = geometry


dirname = os.path.dirname(__file__)
weather_stations_file_path = os.path.join(
    dirname, 'weather-stations.json')

with open(weather_stations_file_path) as weather_stations_file:
    json_data = json.load(weather_stations_file)
    results = []
    for station in json_data['weather_stations']:
        results.append(GeoJsonWeatherStation(type="Feature",
                                             properties=WeatherStationProperties(
                                                 code=station['code'],
                                                 name=station['name'],
                                                 ecodivision_name=station['ecodivision_name'],
                                                 core_season=station['core_season']).__dict__,
                                             geometry=WeatherStationGeometry(
                                                 type="Point",
                                                 coordinates=[station['long'], station['lat']]).__dict__).__dict__)
print(json.dumps(results))

with open('new-weather-stations.json', 'w') as outfile:
    json.dump(results, outfile)
