""" Pre 90th percentile calculator """
import os
import json
import pandas as pd

# pylint: disable=import-error, invalid-name

RECENT_YEAR = 2019  # the most recent year that has the core fire season recorded
RANGES = [(1970, RECENT_YEAR), (RECENT_YEAR - 19, RECENT_YEAR),
          (RECENT_YEAR - 9, RECENT_YEAR)]
PERCENTILE = 0.9
NUMBER_OF_DECIMAL_POINT = 5  # for FWI values


def main():
    """ The main entrypoint for pre-generating json daily summaries. """
    # import the CSV into Pandas dataframe
    print('Open file...')
    df = pd.read_csv('csv/DailyWeather.csv')
    print('Split dates into multiple columns...')
    split_dates_into_multiple_cols(df)

    stations = get_stations()

    for start_year, end_year in RANGES:
        year_range = list(range(start_year, end_year + 1))
        year_df = grab_data_in_particular_year_range(df, year_range)

        folder_name = getOutputFolderName(start_year, end_year)

        for station in stations:
            station_code = int(station['code'])
            station_df = year_df[year_df['station_code'] == station_code]

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
    return {
        'ffmc': None,
        'isi': None,
        'bui': None,
        'years': year_range,
        'station': station
    }


def dump_summary_in_json(folder_name: str, station_code: str, summary: dict):
    """ Create a json file with the given summary """
    filename = '{}/{}.json'.format(folder_name, station_code)
    with open(filename, 'w+') as json_file:
        json.dump(summary, json_file, indent=4, allow_nan=False)


def getOutputFolderName(start_year: int, end_year: int) -> str:
    """ Create an output folder and return its name """
    folder_name = "app/data/{}-{}".format(start_year, end_year)
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
    return folder_name


def get_stations() -> list:
    """ Load stations from json """
    with open('app/data/weather_stations.json') as file_handle:
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
    df['weather_date'] = df['weather_date'].apply(str)
    df['year'] = df['weather_date'].apply(lambda x: int(x[:4]))
    df['month'] = df['weather_date'].apply(lambda x: int(x[4:6]))
    df['day'] = df['weather_date'].apply(lambda x: int(x[6:]))


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
    ffmc = df[df['ffmc_valid']].ffmc.quantile(percentile)
    bui = df[df['bui_valid']].bui.quantile(percentile)
    isi = df[df['isi_valid']].isi.quantile(percentile)

    ffmc = round(ffmc, NUMBER_OF_DECIMAL_POINT) if not pd.isna(ffmc) else None
    bui = round(bui, NUMBER_OF_DECIMAL_POINT) if not pd.isna(bui) else None
    isi = round(isi, NUMBER_OF_DECIMAL_POINT) if not pd.isna(isi) else None

    return {'ffmc': ffmc, 'bui': bui, 'isi': isi}


def get_years_for_valid_fwi_values(df) -> list:
    """ List each year that is sorted """
    ffmc_data_years = df[df['ffmc_valid']].year.unique().tolist()
    bui_data_years = df[df['bui_valid']].year.unique().tolist()
    isi_data_years = df[df['isi_valid']].year.unique().tolist()
    # Combine them and remove duplicates
    data_years = list(set(ffmc_data_years) | set(
        bui_data_years) | set(isi_data_years))
    data_years.sort()

    return data_years


if __name__ == '__main__':
    main()
