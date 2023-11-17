""" This module contains "throaway" code for pre-generating a list of stations.

TODO: Remove this module when the Fire Weather Index Calculator uses the correct API as source for data.
"""
import json
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from pathlib import Path
from typing import Generator

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
            core_season = core_seasons.get(ecodivision_name, {}).get('core_season', {})
        else:
            core_season = {"start_month": "5", "start_day": "1", "end_month": "8", "end_day": "31"}

        weather_stations.append({
            "code": row['STATION_CODE'],
            "name": row['STATION_NAME'],
            "lat": row['LATITUDE'],
            "long": row['LONGITUDE'],
            "ecodivision_name": ecodivision_name,
            "core_season": core_season
        })

    # Order stations by name.
    weather_stations.sort(key=lambda station: station['name'])
    return weather_stations

def export_stations_to_json(weather_stations: list, output_path: str):
    """Export weather stations data to a JSON file."""
    with open(output_path, 'w') as json_file:
        # Dump json with an indent making it more human-readable.
        json.dump({'weather_stations': weather_stations}, json_file, indent=2)

def load_all_csv_to_dataframe(all_csv: Generator, filter_dailies:bool = False) -> pd.DataFrame:
    dfs = []

    for csv in all_csv:
        df = pd.read_csv(csv)

        if filter_dailies:
            # DATE_TIME is provided in PST (GMT-8) and does not recognize DST. 
            # Daily records will therefor always show up as “YYYYMMDD12”
            df = df[df['DATE_TIME'].astype(str).str.endswith('12')]
        dfs.append(df)

    all_dailies_df = pd.concat(dfs, ignore_index=True)

    return all_dailies_df

def generate_station_json(input_path: str) -> str:
    base_path = Path(input_path)

    ecodivisions_gdf = gpd.read_file(ECODIVISIONS)
    core_seasons_json = load_json(CORE_SEASONS)

    station_csv_list = base_path.rglob('*STATIONS.csv')
    weather_stations_df = load_all_csv_to_dataframe(station_csv_list)

    filtered_stations_df = filter_stations(weather_stations_df)

    weather_stations = process_stations(filtered_stations_df, ecodivisions_gdf, core_seasons_json)

    # Export processed stations to JSON
    export_path = R'app/data/weather_stations.json'
    export_stations_to_json(weather_stations, export_path)

    print('Station export complete, {} stations exported.'.format(len(weather_stations)))
    return export_path

if __name__ == "__main__":
    csv_parent_path = '/path/to/parent/BCWS_datamart_historical_wx_obs'
    generate_station_json(csv_parent_path)

