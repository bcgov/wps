import pandas as pd
import json

# --------- INPUT PARAMETERS -----------------
# fire season start and end dates (month and day in numeric format) for location
# May 1 - Aug 31 used for now as MVP
FIRE_SEASON_START_MONTH = 5
FIRE_SEASON_START_DATE = 1
FIRE_SEASON_END_MONTH = 8
FIRE_SEASON_END_DATE = 31

# time range start and end years
# start of 2010 fire season to end of 2019 fire season is 10 years
START_YEAR = 2010
END_YEAR = 2019

# percentile to report out (in decimal format)
PERCENTILE = 0.9
# ------------ end of input parameters ---------

# ---------- GLOBAL VARIABLES ----------------
# import the CSV into Pandas dataframe
print('open file...')
daily_weather_data = pd.read_csv('../DailyWeather.csv')
# initialize empty Pandas Series for storing results
ffmc_percentiles, bui_percentiles, isi_percentiles, data_years = pd.Series(
    [], dtype=float), pd.Series([], dtype=float), pd.Series([], dtype=float), pd.Series([], dtype=object)
# create global Season instance to be used in output
season = {
    'start_month': FIRE_SEASON_START_MONTH,
    'start_day': FIRE_SEASON_START_DATE,
    'end_month': FIRE_SEASON_END_MONTH,
    'end_day': FIRE_SEASON_END_DATE
}
# ----------- end of global variables -------------


# the algorithm
def main():
    parse_weather_dates()
    remove_data_outside_date_range()
    remove_data_outside_fire_season()
    sort_by_weather_station()
    calculate_percentile_per_station()
    list_years_per_station()
    write_output_to_json()


def parse_weather_dates():
    print('parse_weather_dates...')
    # parse weather_date string into 3 columns: yyyy - mm - dd
    daily_weather_data['weather_date'] = daily_weather_data['weather_date'].apply(
        str)
    daily_weather_data['year'] = daily_weather_data['weather_date'].apply(
        lambda x: int(x[:4]))
    daily_weather_data['month'] = daily_weather_data['weather_date'].apply(
        lambda x: int(x[4:6]))
    daily_weather_data['day'] = daily_weather_data['weather_date'].apply(
        lambda x: int(x[6:]))
    return


def remove_data_outside_date_range():
    print('remove_data_outside_date_range...')
    # remove data recorded before START_YEAR
    indexNames = daily_weather_data[daily_weather_data['year']
                                    < START_YEAR].index
    daily_weather_data.drop(indexNames, inplace=True)
    # remove data recorded after END_YEAR
    indexNames = daily_weather_data[daily_weather_data['year']
                                    > END_YEAR].index
    daily_weather_data.drop(indexNames, inplace=True)
    return


def remove_data_outside_fire_season():
    print('remove_data_outside_fire_season...')
    # remove data recorded outside of fire season
    indexNames = daily_weather_data[daily_weather_data['month']
                                    < FIRE_SEASON_START_MONTH].index
    daily_weather_data.drop(indexNames, inplace=True)
    indexNames = daily_weather_data[daily_weather_data['month']
                                    > FIRE_SEASON_END_MONTH].index
    daily_weather_data.drop(indexNames, inplace=True)
    indexNames = daily_weather_data[(daily_weather_data['month'] == FIRE_SEASON_START_MONTH) & (
        daily_weather_data['day'] < FIRE_SEASON_START_DATE)].index
    daily_weather_data.drop(indexNames, inplace=True)
    indexNames = daily_weather_data[(daily_weather_data['month'] == FIRE_SEASON_END_MONTH) & (
        daily_weather_data['day'] > FIRE_SEASON_END_DATE)].index
    daily_weather_data.drop(indexNames, inplace=True)
    return


def sort_by_weather_station():
    print('sort_by_weather_station...')
    # sort the dataframe by station ID
    daily_weather_data.sort_values(by=['station_code'], inplace=True)
    return


def calculate_percentile_per_station():
    print('calculate_percentile_per_station...')
    global ffmc_percentiles, bui_percentiles, isi_percentiles
    ffmc_percentiles = daily_weather_data.groupby(
        'station_code').ffmc.quantile(PERCENTILE)
    bui_percentiles = daily_weather_data.groupby(
        'station_code').bui.quantile(PERCENTILE)
    isi_percentiles = daily_weather_data.groupby(
        'station_code').isi.quantile(PERCENTILE)
    return


def list_years_per_station():
    print('list_years_per_station...')
    # data_years will be a pandas dataframe, which you can kind of think of as a
    # dictionary containing a list of integers.
    global data_years
    data_years = daily_weather_data.groupby('station_code').year.unique()
    data_years.apply(lambda x: x.sort())


def write_output_to_json():
    print('write_output_to_json...')
    global season, year_range, station_summary_dict
    for index, value in ffmc_percentiles.items():
        station_summary = {
            'FFMC': ffmc_percentiles[index],
            'ISI': isi_percentiles[index],
            'BUI': bui_percentiles[index],
            'season': season,
            'years': [int(year) for year in data_years[index]],
            'station_name':
                daily_weather_data.loc[daily_weather_data['station_code']
                                       == index, 'station_name'].iloc[0]
        }
        output_filename = "../data/" + str(index) + ".json"
        with open(output_filename, 'w+') as json_file:
            json.dump(station_summary, json_file, indent=4)

    return


if __name__ == '__main__':
    main()
