""" This is a "throway" script used to export data in an Access database to .csv as a stopgap solution
until such time as the Fire Weather Index calculator is communicating directly to the Wildfire One API.

NOTE: This script will only work in an environment with an Access ODBC driver for PyODBC (in other words,
it will only work on a computer running Windows).

TODO: Remove this script once API is talking directly to the final Wildfire API.
"""
import csv
import os

import pyodbc  # pylint: disable=import-error

# This module contains some very basic code for exporting CSV files from an access database.


# following instructions from https://github.com/mkleehammer/pyodbc/wiki/Connecting-to-Microsoft-Access
# Do a visual check for access odbc drivers:
# i had to install the 32bit driver (https://www.microsoft.com/en-US/download/details.aspx?id=13255) to get
# accdb
# pylint: disable=c-extension-no-member
DRIVERS = [x for x in pyodbc.drivers() if x.startswith('Microsoft Access Driver')]
# pylint: enable=c-extension-no-member
print(DRIVERS)


def export_table(cursor, table, sql):
    """ Function to export all rows from sql query to csv file. """
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


def main():
    """ Entry point for exporting Access to csv """
    database_location = os.path.join(os.getcwd(), 'BCFireWeather2019_DailyAllStns')
    conn_str = 'DRIVER={{Microsoft Access Driver (*.mdb)}};DBQ={};'.format(database_location)
    with pyodbc.connect(conn_str) as connection:
        with connection.cursor() as cursor:
            export_table(cursor, 'Station_BC',
                         'SELECT * FROM Station_BC ORDER BY station_code')
            export_table(cursor, 'DailyWeather',
                         'SELECT * FROM DailyWeather ORDER BY station_code, weather_date')


if __name__ == '__main__':
    main()
