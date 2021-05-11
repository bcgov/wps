import os
import sys
from os.path import isfile, join
import json

"""
Helper script to rename files downloaded from BC FireWeather P1 website.
Files from P1 are named simply with timestamp of date and time of download,
but it's much more convenient to have these files named by weather station code.

This script iterates through the files in a given directory, reads the "display_name"
in the second line of the CSV file, gets the corresponding station_code associated with
the display_name, and renames that CSV file with the station_code.
"""

"""
USAGE:
`python3 ./convert_filename_timestamp_to_code.py {DIRECTORY_PATH}`

DIRECTORY_PATH needs to be an absolute filepath, and  will be treated as a literal string - 
i.e., you should not include '*' when trying to get subdirectories.
"""

dir_name = sys.argv[1]
subfolders = [d.path for d in os.scandir(dir_name) if d.is_dir()]

print('\nRetrieving files from these subfolders:\n{}'.format(subfolders))

if (len(subfolders) == 0):
    print('No subfolders found. Exiting.')
    exit()

# load weather_stations.json into JSON object
with open('../app/data/weather_stations.json', 'r') as j:
    station_dict = json.load(j)
    stations_list = station_dict['weather_stations']
    station_names_to_codes_dict = {}
    for s in stations_list:
        station_names_to_codes_dict[s.get('name')] = s.get('code')

error_counter = 0
for subdir in subfolders:
    print('\nProcessing directory {}'.format(subdir))
    original_file_names = [f for f in os.listdir(subdir) if isfile(join(subdir, f))]

    file_counter = 0
    for og_file_name in original_file_names:
        with open(os.path.join(subdir, og_file_name), 'r') as fp:
            try:
                next(fp)            # skip the first line - it's the column names
                line = next(fp)     # line = contents of second line of file fp
                display_name = line.split(',')[0]
                code = station_names_to_codes_dict.get(display_name)

                # rename the file
                new_filename = code + '.csv'
                os.rename(join(subdir, og_file_name), join(subdir, new_filename))

                file_counter += 1
            except:
                error_counter += 1
                print('Something went wrong processing {}/{}'.format(subdir, og_file_name))

    print('Processed {} files in {}'.format(file_counter, subdir))

print('Finished processing {} with {} errors.'.format(dir_name, error_counter))
