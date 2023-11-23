""" This module contains code for generating a weather_stations.json file on it's own. This file contains all active and historical 
stations along with metadata.
"""
import json
import asyncio
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from scripts.percentile_calculator.s3_to_dataframe import load_all_csv_to_dataframe, get_csv_list_from_s3, filter_wx_and_station_csv

ECODIVISIONS = R'app/data/ERC_ECODIV_polygon/ERC_ECODIV_polygon.shp'
CORE_SEASONS = R'app/data/ecodivisions_core_seasons.json'

def load_json(json_path: str) -> dict:
    """Load from a JSON file."""
    with open(json_path) as file_handle:
        return json.load(file_handle)

def filter_stations(station_df: pd.DataFrame) -> pd.DataFrame:
    """Filter stations based on specific criteria."""
    station_df = station_df.drop_duplicates('STATION_CODE', keep='first')
    
    # Station names that start with ZZ are not active, and must be skipped.
    # Quick deploy (temporary) stations are marked QD at the end
    # Remove stations ending with SF and (WIND), which don't have valid fwi values
    regex = "^(ZZ)|(.*QD)$|(.*SF)$|(.*\(WIND\))"
    return station_df[~station_df['STATION_NAME'].str.match(regex)]

def fetch_ecodivision_name(latitude: float, longitude: float, ecodivisions: gpd.GeoDataFrame):
    """Returns the ecodivision name for a given lat/long coordinate."""
    station_coord = Point(float(longitude), float(latitude))
    for _, ecodivision_row in ecodivisions.iterrows():
        geom = ecodivision_row['geometry']
        if station_coord.within(geom):
            return ecodivision_row['CDVSNNM']
    return None

def process_stations(station_df: pd.DataFrame, ecodivisions: gpd.GeoDataFrame, core_seasons: dict) -> list:
    """Process weather stations and export data."""
    weather_stations = []

    for _, row in station_df.iterrows():
        # Hard-coded fix for station 447 (WATSON LAKE FS) in the Yukon, ecodivision name has to be hard-coded
        if row['STATION_CODE'] == "447":
            ecodivision_name = "SUB-ARCTIC HIGHLANDS"
        else:
            ecodivision_name = fetch_ecodivision_name(row['LATITUDE'], row['LONGITUDE'], ecodivisions)

        if ecodivision_name is not None:
            core_season = core_seasons.get(ecodivision_name, core_seasons['DEFAULT']).get('core_season')
        else:
            core_season = core_seasons['DEFAULT']['core_season']

        weather_stations.append({
            "code": row['STATION_CODE'],
            "name": row['STATION_NAME'],
            "lat": row['LATITUDE'],
            "long": row['LONGITUDE'],
            "ecodivision_name": ecodivision_name,
            "core_season": core_season,
            "elevation": int(row['ELEVATION_M'])
        })

    # Order stations by name.
    weather_stations.sort(key=lambda station: station['name'])
    return weather_stations

def export_stations_to_json(weather_stations: list, output_path: str):
    """Export weather stations data to a JSON file."""
    with open(output_path, 'w') as json_file:
        # Dump json with an indent making it more human-readable.
        json.dump({'weather_stations': weather_stations}, json_file, indent=2)


async def generate_station_json(station_csv_list: list) -> str:
    ecodivisions_gdf = gpd.read_file(ECODIVISIONS)
    core_seasons_json = load_json(CORE_SEASONS)
    
    weather_stations_df = load_all_csv_to_dataframe(station_csv_list)

    filtered_stations_df = filter_stations(weather_stations_df)

    weather_stations = process_stations(filtered_stations_df, ecodivisions_gdf, core_seasons_json)

    # Export processed stations to JSON
    export_path = R'app/data/weather_stations.json'
    export_stations_to_json(weather_stations, export_path)

    print('Station export complete, {} stations exported.'.format(len(weather_stations)))
    return export_path

if __name__ == "__main__":
    all_csv_from_s3 = asyncio.run(get_csv_list_from_s3(2023))
    _, station_list = filter_wx_and_station_csv(all_csv_from_s3)
    asyncio.run(generate_station_json(station_list))

