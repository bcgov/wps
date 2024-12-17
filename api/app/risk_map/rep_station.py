"""
Includes functions for representative stations for fires
"""

from app.schemas.risk import FireShapeStation
from app.stations import get_detailed_stations, get_stations_as_geojson
from shapely.geometry import Point
import geopandas


async def get_stations_detailed_gdf(time_of_interest):
    weather_stations = await get_detailed_stations(time_of_interest)

    # Extract data for GeoDataFrame
    records = []
    for feature in weather_stations:
        geom = Point(feature.geometry.coordinates)  # Convert GeoJSON to Shapely geometry
        data = feature.dict()  # Convert Pydantic model to a dictionary
        data["geometry"] = geom  # Replace GeoJSON with Shapely geometry
        records.append(data)

    stations_gdf = geopandas.GeoDataFrame([{"code": r["properties"]["code"], "name": r["properties"]["name"], "geometry": r["geometry"]} for r in records])
    stations_gdf.set_crs(epsg=4326, inplace=True)

    return stations_gdf


async def get_stations_gdf():
    weather_stations = await get_stations_as_geojson()

    # Extract data for GeoDataFrame
    records = []
    for feature in weather_stations:
        geom = Point(feature.geometry.coordinates)  # Convert GeoJSON to Shapely geometry
        data = feature.dict()  # Convert Pydantic model to a dictionary
        data["geometry"] = geom  # Replace GeoJSON with Shapely geometry
        records.append(data)

    stations_gdf = geopandas.GeoDataFrame([{"code": r["properties"]["code"], "name": r["properties"]["name"], "geometry": r["geometry"]} for r in records])
    stations_gdf.set_crs(epsg=4326, inplace=True)

    return stations_gdf


async def closest_stations(fire_perim_gdf):
    """
    Returns the nearest station for each fire perimeter

    :param fire_perim_gdf: fire perimeter geodataframe
    :return: fire perimeter geodataframe annotated with the nearest fire weather station metadata
    """
    stations_gdf = await get_stations_gdf()
    fire_perim_closest_station_gdf = geopandas.sjoin_nearest(fire_perim_gdf, stations_gdf, how="left", distance_col="distance")
    fire_perim_closest_station_gdf = fire_perim_closest_station_gdf[["FIRE_NUMBER", "code"]]
    return fire_perim_closest_station_gdf


async def get_fire_perimeter_representative_stations(fire_perim_gdf):
    representative_stations = await closest_stations(fire_perim_gdf)
    rep_set = set()
    rep_stations_list = []
    for fire, code in zip(representative_stations["FIRE_NUMBER"], representative_stations["code"]):
        if fire not in rep_set:
            rep_stations_list.append(FireShapeStation(fire_number=fire, station_code=code))
            rep_set.add(fire)

    return rep_stations_list


async def get_hotspots_nearest_station(hotspot_gdf, time_of_interest):
    stations_gdf = await get_stations_detailed_gdf(time_of_interest)
    hotspot_closest_station_gdf = geopandas.sjoin_nearest(hotspot_gdf, stations_gdf, how="left", distance_col="distance")
    return hotspot_closest_station_gdf
