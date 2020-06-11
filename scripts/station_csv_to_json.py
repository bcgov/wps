""" This module contains "throaway" code for pre-generating a list of stations.

TODO: Remove this module when the Fire Weather Index Calculator uses the correct API as source for data.
"""
import csv
import json
import re

with open('csv/Station_BC.csv', 'r') as csvfile:
    READER = csv.reader(csvfile, dialect=csv.unix_dialect)

    HEADER = next(READER)
    STATION_CODE = HEADER.index('station_code')
    STATION_NAME = HEADER.index('station_name')
    STATION_CATEGORY = HEADER.index('station_category')
    STATION_LATITUDE = HEADER.index('latitude')
    STATION_LONGITUDE = HEADER.index('longitude')

    WEATHER_STATIONS = []

    # Keep track of station count for debug purposes.
    STATION_COUNT = 0
    for row in READER:
        # We're only interested in permanent, active weather stations
        # Active stations are either marked as 'active' in the station_category row.
        # Some stations are incorrectly labeled 'active', station names that start
        # with ZZ are not active, and must be skipped.
        # Quick deploy (temporary) stations are marked QD at the end
        regex = re.compile('^(ZZ)|(.*QD)$', re.I)
        if row[STATION_CATEGORY] == 'active':
            if regex.match(row[STATION_NAME]):
                print('Skipping {}:{}'.format(
                    row[STATION_CODE], row[STATION_NAME]))
                continue
            STATION_COUNT = STATION_COUNT + 1
            WEATHER_STATIONS.append(
                {
                    "code": row[STATION_CODE],
                    "name": row[STATION_NAME],
                    "lat": row[STATION_LATITUDE],
                    "long": row[STATION_LONGITUDE]
                }
            )

    # Order stations by name.
    WEATHER_STATIONS.sort(key=lambda station: station['name'])

    with open('app/data/weather_stations.json', 'w') as json_file:
        # Dump json with an indent making it more human readable.
        json.dump({
            'weather_stations': WEATHER_STATIONS
        }, json_file, indent='  ')

    print('Station export complete, {} stations exported.'.format(STATION_COUNT))
