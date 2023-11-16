""" Pre 90th percentile calculator """
import os
import json
import pandas as pd
from pathlib import Path
from scripts.station_csv_to_json import load_all_csv_to_dataframe


RECENT_YEAR = 2023  # the most recent year that has the core fire season recorded
RANGES = [(RECENT_YEAR - 29, RECENT_YEAR), (RECENT_YEAR - 19, RECENT_YEAR),
          (RECENT_YEAR - 9, RECENT_YEAR)]
PERCENTILE = 0.9
NUMBER_OF_DECIMAL_POINT = 5  # for FWI values

BASE = Path(R'/path/to/parent/BCWS_datamart_historical_wx_obs')

def main():
    """ The main entrypoint for pre-generating json daily summaries. """
    wx_obs_csv_list = BASE.rglob('*OBS.csv')
    df = load_all_csv_to_dataframe(wx_obs_csv_list, filter_dailies=True)

    print('Split dates into multiple columns...')
    split_dates_into_multiple_cols(df)

    stations = get_stations()

    for start_year, end_year in RANGES:
        year_range = list(range(start_year, end_year + 1))
        year_df = grab_data_in_particular_year_range(df, year_range)

        folder_name = get_output_foldername(start_year, end_year)

        for station in stations:
            station_code = int(station['code'])
            station_df = year_df[year_df['STATION_CODE'] == station_code]

            if station_df.empty:
                print('Data not available for {} creating empty summary...'.format(
                    station_code))
                empty_summary = create_null_summary(station, year_range)
                dump_summary_in_json(folder_name, station_code, empty_summary)
                continue

            season = get_core_fire_season(station)
            remove_data_outside_fire_season(station_df, season)
            percentiles = calculate_percentile(station_df, PERCENTILE)

            years = get_years_for_valid_fwi_values(station_df)

            summary = {
                'ffmc': percentiles['ffmc'],
                'isi': percentiles['isi'],
                'bui': percentiles['bui'],
                'years': years,
                'station': station
            }

            dump_summary_in_json(folder_name, station_code, summary)

        print('--- Done creating data under {} folder ---'.format(folder_name))

def create_null_summary(station, year_range):
    """ Create an empty summary """
    return {
        'ffmc': None,
        'isi': None,
        'bui': None,
        'years': year_range,
        'station': station
    }


def dump_summary_in_json(folder_name: str, station_code: int, summary: dict):
    """ Create a json file with the given summary """
    filename = '{}/{}.json'.format(folder_name, station_code)
    with open(filename, 'w+') as json_file:
        json.dump(summary, json_file, indent=4, allow_nan=False)


def get_output_foldername(start_year: int, end_year: int) -> str:
    """ Create an output folder and return its name """
    folder_name = "api/app/data/{}-{}".format(start_year, end_year)
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
    return folder_name


def get_stations() -> list:
    """ Load stations from json """
    with open('api/app/data/weather_stations.json') as file_handle:
        return json.load(file_handle)['weather_stations']


def get_core_fire_season(station) -> dict:
    """ Read the core fire season and return them in dict """
    return {
        'start_month': int(station['core_season']['start_month']),
        'start_day': int(station['core_season']['start_day']),
        'end_month': int(station['core_season']['end_month']),
        'end_day': int(station['core_season']['end_day']),
    }


def split_dates_into_multiple_cols(df):
    """ Turn weather_date into datetime type then create 3 columns, year, month, and day """
    df['DATE_TIME'] = df['DATE_TIME'].apply(str)
    df['year'] = df['DATE_TIME'].apply(lambda x: int(x[:4]))
    df['month'] = df['DATE_TIME'].apply(lambda x: int(x[4:6]))
    df['day'] = df['DATE_TIME'].apply(lambda x: int(x[6:]))


def grab_data_in_particular_year_range(df, year_range: list) -> pd.DataFrame:
    """ Grab data recorded between start_year and end_year. """
    return df[df['year'].isin(year_range)]


def remove_data_outside_fire_season(df, season: dict):
    """ Remove data recorded outside of fire season. """
    outside_month = (df['month'] < season['start_month']) | (
        df['month'] > season['end_month'])
    df.drop(df[outside_month].index, inplace=True)

    before_start = ((df['month'] == season['start_month']) &
                    (df['day'] < season['start_day']))
    df.drop(df[before_start].index, inplace=True)

    after_end = ((df['month'] == season['end_month']) &
                 (df['day'] > season['end_day']))
    df.drop(df[after_end].index, inplace=True)


def calculate_percentile(df, percentile: float) -> dict:
    """ Calculate percentile """
    ffmc = df[df['FINE_FUEL_MOISTURE_CODE'].notnull()]['FINE_FUEL_MOISTURE_CODE'].quantile(percentile)
    bui = df[df['BUILDUP_INDEX'].notnull()]['BUILDUP_INDEX'].quantile(percentile)
    isi = df[df['INITIAL_SPREAD_INDEX'].notnull()]['INITIAL_SPREAD_INDEX'].quantile(percentile)

    ffmc = round(ffmc, NUMBER_OF_DECIMAL_POINT) if not pd.isna(ffmc) else None
    bui = round(bui, NUMBER_OF_DECIMAL_POINT) if not pd.isna(bui) else None
    isi = round(isi, NUMBER_OF_DECIMAL_POINT) if not pd.isna(isi) else None

    return {'ffmc': ffmc, 'bui': bui, 'isi': isi}


def get_years_for_valid_fwi_values(df) -> list:
    """ List each year that is sorted """
    ffmc_data_years = df[df['FINE_FUEL_MOISTURE_CODE'].notnull()].year.unique().tolist()
    bui_data_years = df[df['BUILDUP_INDEX'].notnull()].year.unique().tolist()
    isi_data_years = df[df['INITIAL_SPREAD_INDEX'].notnull()].year.unique().tolist()
    # Combine them and remove duplicates
    data_years = list(set(ffmc_data_years) | set(
        bui_data_years) | set(isi_data_years))
    data_years.sort()

    return data_years


if __name__ == '__main__':
    main()
