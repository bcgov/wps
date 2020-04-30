""" This module contains "throwaway" code for pre-generating weather station summaries.

TODO: Remove this module when the Fire Weather Index Calculator uses the correct API as source for data.
"""
import os
import json
import pandas as pd  # pylint: disable=import-error

# --------- INPUT PARAMETERS -----------------
# fire season start and end dates (month and day in numeric format) for location
# May 1 - Aug 31 used for now as MVP
FIRE_SEASON_START_MONTH = 5
FIRE_SEASON_START_DATE = 1
FIRE_SEASON_END_MONTH = 8
FIRE_SEASON_END_DATE = 31

# time range start and end years
# start of 1970 fire season to end of 2019 fire season is 50 years
# start of 2000 fire season to end of 2019 fire season is 20 years
# start of 2010 fire season to end of 2019 fire season is 10 years
RANGES = ((1970, 2019), (2000, 2019), (2010, 2019))

# percentile to report out (in decimal format)
PERCENTILE = 0.9
# ------------ end of input parameters ---------

# ---------- GLOBAL VARIABLES ----------------
# import the CSV into Pandas dataframe
print('open file...')
DAILY_WEATHER_DATA = pd.read_csv('../DailyWeather.csv')
# ----------- end of global variables -------------


def main():
    """ The main entrypoint for pre-generating json daily summaries. """
    for date_range in RANGES:
        weather_stations = stations_json_to_dict()
        parse_weather_dates()
        remove_data_outside_date_range(date_range)
        remove_data_outside_fire_season()
        percentiles = calculate_percentile_per_station()
        data_years = list_years_per_station()
        write_output_to_json(date_range, weather_stations,
                             data_years, percentiles)


def stations_json_to_dict():
    """ Load stations from json

    Returns: Dictionary containing list of stations.
    """
    with open('../data/weather_stations.json') as file_handle:
        return json.load(file_handle)['weather_stations']


def parse_weather_dates():
    """ Parse weather_date string into 3 columns: yyyy - mm - dd """
    print('parse_weather_dates...')
    DAILY_WEATHER_DATA['weather_date'] = DAILY_WEATHER_DATA['weather_date'].apply(
        str)
    DAILY_WEATHER_DATA['year'] = DAILY_WEATHER_DATA['weather_date'].apply(
        lambda x: int(x[:4]))
    DAILY_WEATHER_DATA['month'] = DAILY_WEATHER_DATA['weather_date'].apply(
        lambda x: int(x[4:6]))
    DAILY_WEATHER_DATA['day'] = DAILY_WEATHER_DATA['weather_date'].apply(
        lambda x: int(x[6:]))


def remove_data_outside_date_range(date_range):
    """ Remove data recorded before START_YEAR or after END_YEAR. """
    print('remove_data_outside_date_range...')
    index = DAILY_WEATHER_DATA[(DAILY_WEATHER_DATA['year'] < date_range[0]) | (
        DAILY_WEATHER_DATA['year'] > date_range[1])].index
    DAILY_WEATHER_DATA.drop(index, inplace=True)


def remove_data_outside_fire_season():
    """ Remove data recorded outside of fire season. """
    print('remove_data_outside_fire_season...')
    index = (DAILY_WEATHER_DATA['month'] < FIRE_SEASON_START_MONTH) | (
        DAILY_WEATHER_DATA['month'] > FIRE_SEASON_END_MONTH)
    index = DAILY_WEATHER_DATA[index].index
    DAILY_WEATHER_DATA.drop(index, inplace=True)
    index = DAILY_WEATHER_DATA[(DAILY_WEATHER_DATA['month'] == FIRE_SEASON_START_MONTH) & (
        DAILY_WEATHER_DATA['day'] < FIRE_SEASON_START_DATE)].index
    DAILY_WEATHER_DATA.drop(index, inplace=True)
    index = DAILY_WEATHER_DATA[(DAILY_WEATHER_DATA['month'] == FIRE_SEASON_END_MONTH) & (
        DAILY_WEATHER_DATA['day'] > FIRE_SEASON_END_DATE)].index
    DAILY_WEATHER_DATA.drop(index, inplace=True)


def calculate_percentile_per_station():
    """ Calculate percentile per weather station.

    Returns:
        dict: Containing percentiles for ffmc, bui and isi per station. """
    print('calculate_percentile_per_station...')
    ffmc_percentiles = DAILY_WEATHER_DATA.groupby(
        'station_code').ffmc.quantile(PERCENTILE)
    bui_percentiles = DAILY_WEATHER_DATA.groupby(
        'station_code').bui.quantile(PERCENTILE)
    isi_percentiles = DAILY_WEATHER_DATA.groupby(
        'station_code').isi.quantile(PERCENTILE)
    return {'ffmc': ffmc_percentiles, 'bui': bui_percentiles, 'isi': isi_percentiles}


def list_years_per_station():
    """ List data years per station.

    Returns:
        Series: pandas dataframe, which you can kind of think of as a dictionary containing a list of
        integers.
    """
    print('list_years_per_station...')
    data_years = DAILY_WEATHER_DATA.groupby('station_code').year.unique()
    data_years.apply(lambda x: x.sort())
    return data_years


def write_output_to_json(date_range, weather_stations, data_years, percentiles):
    """ Write output to json file. """
    print('write_output_to_json...')
    # create season instance to be used in output
    season = {
        'start_month': FIRE_SEASON_START_MONTH,
        'start_day': FIRE_SEASON_START_DATE,
        'end_month': FIRE_SEASON_END_MONTH,
        'end_day': FIRE_SEASON_END_DATE
    }
    for weath_stat in weather_stations:
        key = weath_stat['code']
        try:
            station_summary = {
                'ffmc': percentiles['ffmc'][int(key)],
                'isi': percentiles['isi'][int(key)],
                'bui': percentiles['bui'][int(key)],
                'season': season,
                'years': [int(year) for year in data_years[int(key)]],
                'station': {'code': key, 'name': weath_stat['name']}
            }
            output_folder = "../data/{}-{}".format(
                date_range[0], date_range[1])
            if not os.path.exists(output_folder):
                os.mkdir(output_folder)
            output_filename = output_folder + "/" + key + ".json"
            with open(output_filename, 'w+') as json_file:
                json.dump(station_summary, json_file, indent=4)
        except KeyError:
            print('Data not available for ' + key)


if __name__ == '__main__':
    main()
