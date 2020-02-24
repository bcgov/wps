import csv
import json

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
        # We're only interested in active weather stations.
        if row[station_category] == 'active':
            station_count = station_count + 1
            weather_stations.append(
                {
                    "code": row[station_code],
                    "name": row[station_name]
                }
            )

    with open('weather_stations.json', 'w') as json_file:
        json.dump({
            'weather_stations': weather_stations
        }, json_file)

    print('Station export complete, {} stations exported.'.format(station_count))
