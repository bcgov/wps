""" This module contains "throaway" code for pre-generating a list of stations.

TODO: Remove this module when the Fire Weather Index Calculator uses the correct API as source for data.
"""
import csv
import json
import re
import geopandas
from shapely.geometry import Point


def fetch_ecodivision_name(latitude: str, longitude: str, ecodivisions: geopandas.GeoDataFrame):
    """ Returns the ecodivision name for a given lat/long coordinate """
    station_coord = Point(float(longitude), float(latitude))
    for _, ecodivision_row in ecodivisions.iterrows():
        geom = ecodivision_row['geometry']
        if station_coord.within(geom):
            return ecodivision_row['CDVSNNM']
    return None


with open('csv/Station_BC_June2020.csv', 'r') as csvfile:
    rows = csv.reader(csvfile, dialect=csv.unix_dialect)

    header = next(rows)
    code = header.index('station_code')
    name = header.index('station_name')
    station_category = header.index('station_category')
    lat = header.index('latitude')
    long = header.index('longitude')

    weather_stations = []

    ECODIVISIONS = geopandas.read_file(
        'data/ERC_ECODIV_polygon/ERC_ECODIV_polygon.shp')
    with open('data/ecodivisions_core_seasons.json') as file_handle:
        CORE_SEASONS = json.load(file_handle)

    # Keep track of station count for debug purposes.
    station_count = 0
    for row in rows:
        # We're only interested in permanent, active weather stations
        # Active stations are either marked as 'active' in the station_category row.
        if row[station_category] != 'active':
            continue

        # Some stations are incorrectly labeled 'active', station names that start
        # with ZZ are not active, and must be skipped.
        # Quick deploy (temporary) stations are marked QD at the end
        # Remove stations ending with SF and (WIND), which don't have valid fwi values
        regex = re.compile(r"^(ZZ)|(.*QD)$|(.*SF)$|(.*\(WIND\))", re.I)
        if regex.match(row[name]):
            print('Skipping {}:{}'.format(row[code], row[name]))
            continue

        station_count = station_count + 1

        # hacky fix for station 447 (WATSON LAKE FS), which is in the Yukon
        # so ecodivision name has to be hard-coded
        if row[code] == "447":
            ecodivision_name = "SUB-ARCTIC HIGHLANDS"
        else:
            ecodivision_name = fetch_ecodivision_name(
                row[lat], row[long], ECODIVISIONS)

        if ecodivision_name is not None:
            core_season = CORE_SEASONS[ecodivision_name]['core_season']
        else:
            core_season = {"start_month": "5", "start_day": "1",
                           "end_month": "8", "end_day": "31"}

        weather_stations.append(
            {
                "code": row[code],
                "name": row[name],
                "lat": row[lat],
                "long": row[long],
                "ecodivision_name": ecodivision_name,
                "core_season": core_season
            }
        )

    # Order stations by name.
    weather_stations.sort(key=lambda station: station['name'])

    with open('app/data/weather_stations.json', 'w') as json_file:
        # Dump json with an indent making it more human readable.
        json.dump({'weather_stations': weather_stations}, json_file, indent=2)

    print('Station export complete, {} stations exported.'.format(station_count))
