import sys
import csv

import pyodbc

# This module contains some very basic code for exporting CSV files from an access database.


# following instructions from https://github.com/mkleehammer/pyodbc/wiki/Connecting-to-Microsoft-Access
# Do a visual check for access odbc drivers:
# i had to install the 32bit driver to get accdb (https://www.microsoft.com/en-US/download/details.aspx?id=13255)
[print(x) for x in pyodbc.drivers() if x.startswith('Microsoft Access Driver')]


def export_table(cursor, table, sql):
    # Get the field names
    fieldnames = []
    for row in cursor.columns(table=table):
        fieldnames.append(row.column_name)

    # Open CSV writer
    with open('{}.csv'.format(table), 'w') as csvfile:
        writer = csv.writer(csvfile, dialect=csv.unix_dialect)

        # Write field names
        writer.writerow(fieldnames)

        # Select rows
        cursor.execute(sql)
        # Grab 1000 at a time...
        rows = cursor.fetchmany(1000)
        rows_processed = 0
        while rows:
            for row in rows:
                # Write a row
                writer.writerow(row)
                # Some debug info so we don't think it's frozen
                rows_processed = rows_processed + 1
                if rows_processed % 10000 == 0:
                    print('BUSY: rows processed: {}'.format(rows_processed))
            rows = cursor.fetchmany(100)
        print('DONE: rows processed: {}'.format(rows_processed))


conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb)};'
    r'DBQ=C:\Users\Sybrand\Workspace\wps-api\scripts\BCFireWeather2019_DailyAllStns;'
    )
with pyodbc.connect(conn_str) as connection:
    with connection.cursor() as cursor:
        export_table(cursor, 'Station_BC', 'SELECT * FROM Station_BC ORDER BY station_code')
        export_table(cursor, 'DailyWeather', 'SELECT * FROM DailyWeather ORDER BY station_code, weather_date')
