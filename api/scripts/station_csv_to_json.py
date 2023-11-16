""" This module contains "throaway" code for pre-generating a list of stations.

TODO: Remove this module when the Fire Weather Index Calculator uses the correct API as source for data.
"""
import json
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
from typing import Generator
from pathlib import Path

def load_json(json_path):
    """Load from a JSON file."""
    with open(json_path) as file_handle:
        return json.load(file_handle)

def filter_stations(station_df):
    """Filter stations based on specific criteria."""
    station_df = station_df.drop_duplicates('STATION_CODE', keep='first')
    
    regex = "^(ZZ)|(.*QD)$|(.*SF)$|(.*\(WIND\))"
    return station_df[~station_df['STATION_NAME'].str.match(regex)]

def fetch_ecodivision_name(latitude, longitude, ecodivisions):
    """Returns the ecodivision name for a given lat/long coordinate."""
    station_coord = Point(float(longitude), float(latitude))
    for _, ecodivision_row in ecodivisions.iterrows():
        geom = ecodivision_row['geometry']
        if station_coord.within(geom):
            return ecodivision_row['CDVSNNM']
    return None

def process_stations(station_df, ecodivisions, core_seasons):
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

def export_stations_to_json(weather_stations, output_path):
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

def main():
    base_path = Path(R'/Users/breedwar/Downloads/BCWS_datamart_historical_wx_obs')

    station_csv_list = base_path.rglob('*STATIONS.csv')
    # Load ecodivisions shapefile and core seasons JSON
    ECODIVISIONS = gpd.read_file('api/app/data/ERC_ECODIV_polygon/ERC_ECODIV_polygon.shp')
    CORE_SEASONS = load_json('api/app/data/ecodivisions_core_seasons.json')

    # Load weather stations DataFrame from CSV
    weather_stations_df = load_all_csv_to_dataframe(station_csv_list)

    # Process and filter stations
    filtered_stations_df = filter_stations(weather_stations_df)

    # Process stations, get weather stations data
    weather_stations = process_stations(filtered_stations_df, ECODIVISIONS, CORE_SEASONS)

    # Export processed stations to JSON
    export_stations_to_json(weather_stations, 'api/app/data/weather_stations.json')

    print('Station export complete, {} stations exported.'.format(len(weather_stations)))

if __name__ == "__main__":
    main()

