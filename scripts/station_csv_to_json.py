import csv
import json
import re

with open('Station_BC.csv', 'r') as csvfile:
    reader = csv.reader(csvfile, dialect=csv.unix_dialect)

    header = next(reader)
    station_code = header.index('station_code')
    station_name = header.index('station_name')
    station_category = header.index('station_category')

    weather_stations = []

    # Keep track of station count for debug purposes.
    station_count = 0
    for row in reader:
        # We're only interested in permanent, active weather stations
        # Active stations are either marked as 'active' in the station_category row.
        # Some stations are incorrectly labeled 'active', station names that start
        # with ZZ are not active, and must be skipped.
        # Quick deploy (temporary) stations are marked QD at the end
        regex = re.compile('^(ZZ)|(.*QD)$', re.I)
        if row[station_category] == 'active':
            if regex.match(row[station_name]):
                print('Skipping {}:{}'.format(row[station_code], row[station_name]))
                continue
            station_count = station_count + 1
            weather_stations.append(
                {
                    "code": row[station_code],
                    "name": row[station_name]
                }
            )

    # Order stations by name.
    weather_stations.sort(key=lambda station: station['name'])

    with open('weather_stations.json', 'w') as json_file:
        # Dump json with an indent making it more human readable.
        json.dump({
            'weather_stations': weather_stations
        }, json_file, indent=' ')

    print('Station export complete, {} stations exported.'.format(station_count))
